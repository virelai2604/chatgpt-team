# app/api/forward_openai.py

from __future__ import annotations

import logging
import os
from typing import Any, Dict, Mapping, Optional

import httpx
from fastapi import HTTPException, Request, Response
from fastapi.responses import StreamingResponse

from app.core.config import settings

logger = logging.getLogger("relay")

# Single source of truth – use Pydantic settings (P4 core plan)
OPENAI_API_BASE: str = str(settings.OPENAI_API_BASE).rstrip("/")
OPENAI_API_KEY: str = settings.OPENAI_API_KEY

# Fallback timeout in seconds if not configured on Settings
_DEFAULT_PROXY_TIMEOUT = float(os.getenv("PROXY_TIMEOUT", os.getenv("RELAY_TIMEOUT", "120")))
PROXY_TIMEOUT: float = getattr(settings, "PROXY_TIMEOUT", _DEFAULT_PROXY_TIMEOUT)


def _filter_request_headers(headers: Mapping[str, str]) -> Dict[str, str]:
    """
    Drop hop-by-hop headers and downstream Authorization before forwarding.

    We always inject our own Authorization header, derived from
    OPENAI_API_KEY, so the relay never forwards arbitrary client secrets
    upstream.
    """
    blocked = {
        "host",
        "content-length",
        "connection",
        "keep-alive",
        "proxy-authenticate",
        "proxy-authorization",
        "te",
        "trailers",
        "transfer-encoding",
        "upgrade",
    }

    out: Dict[str, str] = {}
    for name, value in headers.items():
        lower = name.lower()
        if lower in blocked:
            continue
        if lower == "authorization":
            # Always replace with our own Authorization header
            continue
        out[name] = value
    return out


def _filter_response_headers(headers: Mapping[str, str]) -> Dict[str, str]:
    """
    Drop hop-by-hop and compression-related headers from the upstream
    response. We let the ASGI server handle compression and connection reuse.
    """
    blocked = {
        "connection",
        "keep-alive",
        "proxy-authenticate",
        "proxy-authorization",
        "te",
        "trailers",
        "transfer-encoding",
        "upgrade",
        "content-encoding",
        "content-length",
    }

    out: Dict[str, str] = {}
    for name, value in headers.items():
        if name.lower() in blocked:
            continue
        out[name] = value
    return out


def _ensure_api_key() -> None:
    if not OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY is not configured on the relay")
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "message": "OPENAI_API_KEY is not configured on the relay",
                    "type": "server_error",
                    "code": "no_api_key",
                }
            },
        )


def _is_sse_request(request: Request) -> bool:
    """
    Detect Server-Sent Events (SSE) requests by Accept header.

    Responses API uses SSE when the client sends `Accept: text/event-stream`
    and `stream=true` in the JSON body.
    """
    accept = request.headers.get("accept", "")
    return "text/event-stream" in accept.lower()


async def forward_openai_request(
    request: Request,
    *,
    method: Optional[str] = None,
    path_override: Optional[str] = None,
) -> Response:
    """
    Generic forwarder used by all /v1/* routers.

    - Respects the incoming HTTP method (unless overridden).
    - Forwards to OPENAI_API_BASE + path.
    - For SSE (Accept: text/event-stream), streams upstream bytes via
      StreamingResponse.
    """
    _ensure_api_key()

    method = (method or request.method).upper()
    path = path_override or request.url.path

    if not path.startswith("/v1"):
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "message": "Only /v1 paths are proxied",
                    "type": "invalid_request_error",
                }
            },
        )

    headers = _filter_request_headers(request.headers)
    headers["Authorization"] = f"Bearer {OPENAI_API_KEY}"
    # Ensure upstream sends identity-encoded data so we can stream bytes safely
    headers.setdefault("Accept-Encoding", "identity")

    timeout = httpx.Timeout(PROXY_TIMEOUT)

    body = await request.body()
    params = dict(request.query_params)

    is_sse = _is_sse_request(request)

    async with httpx.AsyncClient(base_url=OPENAI_API_BASE, timeout=timeout) as client:
        try:
            if is_sse:
                # SSE: keep connection open and stream upstream bytes directly.
                upstream_cm = client.stream(
                    method,
                    path,
                    params=params,
                    headers=headers,
                    content=body if body else None,
                )
                upstream_response = await upstream_cm.__aenter__()

                resp_headers = _filter_response_headers(upstream_response.headers)
                media_type = upstream_response.headers.get(
                    "content-type", "text/event-stream"
                )

                async def _aiter() -> Any:
                    try:
                        async for chunk in upstream_response.aiter_raw():
                            # Pass through raw SSE wire format untouched
                            if chunk:
                                yield chunk
                        # httpx will send the final "data: [DONE]" from upstream
                    finally:
                        await upstream_cm.__aexit__(None, None, None)

                return StreamingResponse(
                    _aiter(),
                    status_code=upstream_response.status_code,
                    headers=resp_headers,
                    media_type=media_type,
                )

            # Non-streaming JSON / binary
            upstream_response = await client.request(
                method,
                path,
                params=params,
                headers=headers,
                content=body if body else None,
            )
        except httpx.RequestError as exc:  # network / DNS / timeout
            logger.error("Error forwarding request to OpenAI: %r", exc)
            raise HTTPException(
                status_code=502,
                detail={
                    "error": {
                        "message": "Error forwarding request to OpenAI",
                        "type": "server_error",
                        "code": "upstream_request_error",
                        "extra": {"exception": str(exc)},
                    }
                },
            ) from exc

    resp_headers = _filter_response_headers(upstream_response.headers)

    return Response(
        content=upstream_response.content,
        status_code=upstream_response.status_code,
        headers=resp_headers,
        media_type=upstream_response.headers.get("content-type"),
    )
