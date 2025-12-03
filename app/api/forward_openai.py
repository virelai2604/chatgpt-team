# app/api/forward_openai.py

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, Mapping, Optional, Union

import httpx
from fastapi import HTTPException, Request, Response
from fastapi.responses import StreamingResponse

from app.core.config import settings

logger = logging.getLogger("relay")

# Single source of truth – use Pydantic settings (P4 core plan)
OPENAI_API_BASE: str = str(settings.OPENAI_API_BASE).rstrip("/")
OPENAI_API_KEY: str = settings.OPENAI_API_KEY

# Fallback timeout in seconds if not configured on Settings
DEFAULT_PROXY_TIMEOUT = float(os.getenv("PROXY_TIMEOUT", os.getenv("RELAY_TIMEOUT", "120")))
PROXY_TIMEOUT: float = getattr(settings, "PROXY_TIMEOUT", DEFAULT_PROXY_TIMEOUT)


def _filter_request_headers(headers: Mapping[str, str]) -> Dict[str, str]:
    """
    Drop hop-by-hop headers and downstream Authorization before forwarding.

    We will always inject our own Authorization header, derived from
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
    for k, v in headers.items():
        kl = k.lower()
        if kl in blocked:
            continue
        if kl == "authorization":
            # Always replace with our own Authorization header
            continue
        out[k] = v
    return out


def _filter_response_headers(headers: Mapping[str, str]) -> Dict[str, str]:
    """
    Drop hop-by-hop headers and compression-related headers from the upstream
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
    for k, v in headers.items():
        kl = k.lower()
        if kl in blocked:
            continue
        out[k] = v
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
    - Streams SSE transparently when the client sends Accept: text/event-stream.
    """
    _ensure_api_key()

    method = (method or request.method).upper()
    path = path_override or request.url.path

    if not path.startswith("/v1"):
        raise HTTPException(
            status_code=404,
            detail={"error": {"message": "Only /v1 paths are proxied", "type": "invalid_request_error"}},
        )

    headers = _filter_request_headers(request.headers)
    headers["Authorization"] = f"Bearer {OPENAI_API_KEY}"

    # Preserve OpenAI-Organization, OpenAI-Project, OpenAI-Beta (if provided)
    timeout = httpx.Timeout(PROXY_TIMEOUT)

    body = await request.body()
    params = dict(request.query_params)

    is_sse = _is_sse_request(request)

    async with httpx.AsyncClient(base_url=OPENAI_API_BASE, timeout=timeout) as client:
        try:
            if is_sse:
                # SSE: keep connection open and stream upstream bytes directly.
                upstream = client.stream(
                    method,
                    path,
                    params=params,
                    headers=headers,
                    content=body if body else None,
                )
                upstream_cm = upstream.__aenter__()
                upstream_response = await upstream_cm

                resp_headers = _filter_response_headers(upstream_response.headers)
                media_type = upstream_response.headers.get("content-type", "text/event-stream")

                async def _aiter() -> Any:
                    try:
                        async for chunk in upstream_response.aiter_raw():
                            yield chunk
                    finally:
                        await upstream.__aexit__(None, None, None)

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


async def forward_openai_from_parts(
    method: str,
    path: str,
    *,
    query: Optional[Mapping[str, Any]] = None,
    headers: Optional[Mapping[str, str]] = None,
    body: Optional[Union[str, bytes, Mapping[str, Any], Any]] = None,
    stream: bool = False,
) -> Response:
    """
    Programmatic forwarding used by /v1/actions/openai/forward.

    - `method`: HTTP method ("GET", "POST", etc).
    - `path`: must start with "/v1".
    - `query`: optional query params.
    - `headers`: optional additional headers from caller.
    - `body`: raw bytes/str or JSON-serializable structure.
    - `stream`: when True, stream via SSE (caller must also set appropriate Accept header).
    """
    _ensure_api_key()

    if not path.startswith("/v1"):
        raise HTTPException(
            status_code=400,
            detail={"error": {"message": "path must start with /v1", "type": "invalid_request_error"}},
        )

    method = method.upper()
    base_headers = _filter_request_headers(headers or {})
    base_headers["Authorization"] = f"Bearer {OPENAI_API_KEY}"

    timeout = httpx.Timeout(PROXY_TIMEOUT)
    params = dict(query or {})

    async with httpx.AsyncClient(base_url=OPENAI_API_BASE, timeout=timeout) as client:
        try:
            json_body: Any = None
            content_body: Any = None

            if isinstance(body, (bytes, str)) or body is None:
                content_body = body
            else:
                # Assume JSON-serializable
                json_body = body

            if stream:
                upstream = client.stream(
                    method,
                    path,
                    params=params,
                    headers=base_headers,
                    json=json_body,
                    content=content_body,
                )
                upstream_cm = upstream.__aenter__()
                upstream_response = await upstream_cm

                resp_headers = _filter_response_headers(upstream_response.headers)
                media_type = upstream_response.headers.get("content-type", "text/event-stream")

                async def _aiter() -> Any:
                    try:
                        async for chunk in upstream_response.aiter_raw():
                            yield chunk
                    finally:
                        await upstream.__aexit__(None, None, None)

                return StreamingResponse(
                    _aiter(),
                    status_code=upstream_response.status_code,
                    headers=resp_headers,
                    media_type=media_type,
                )

            upstream_response = await client.request(
                method,
                path,
                params=params,
                headers=base_headers,
                json=json_body,
                content=content_body,
            )
        except httpx.RequestError as exc:
            logger.error("Error forwarding request (from_parts) to OpenAI: %r", exc)
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
