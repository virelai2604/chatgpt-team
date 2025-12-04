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

# ---------------------------------------------------------------------------
# Upstream configuration
# ---------------------------------------------------------------------------

# Base URL for OpenAI (no /v1 suffix – paths below always start with /v1)
OPENAI_API_BASE: str = str(settings.OPENAI_API_BASE).rstrip("/")

# API key used by the relay when forwarding to OpenAI
OPENAI_API_KEY: str = settings.OPENAI_API_KEY

# Timeout (seconds) for upstream OpenAI calls
DEFAULT_PROXY_TIMEOUT = float(os.getenv("PROXY_TIMEOUT", os.getenv("RELAY_TIMEOUT", "120")))
PROXY_TIMEOUT: float = float(getattr(settings, "PROXY_TIMEOUT", DEFAULT_PROXY_TIMEOUT))


# ---------------------------------------------------------------------------
# Header helpers
# ---------------------------------------------------------------------------


def _filter_request_headers(headers: Mapping[str, str]) -> Dict[str, str]:
    """
    Prepare headers for forwarding to OpenAI.

    - Drop hop-by-hop headers that should not cross proxies.
    - Drop downstream Authorization and X-Relay-Key; the relay injects its own.
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
        "x-relay-key",
    }

    out: Dict[str, str] = {}
    for name, value in headers.items():
        lname = name.lower()
        if lname in blocked:
            continue
        if lname == "authorization":
            # Always replace with relay's Authorization header
            continue
        out[name] = value
    return out


def _filter_response_headers(headers: Mapping[str, str]) -> Dict[str, str]:
    """
    Prepare headers coming back from OpenAI before returning to the client.

    We drop hop-by-hop and transport headers; Uvicorn/ASGI will manage
    Content-Length, Transfer-Encoding, and connection reuse.
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
    """
    Ensure the relay has an OpenAI API key configured.
    """
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

    SSE is used by the Responses API when `stream=true` and the client
    requests `Accept: text/event-stream`. See official streaming docs.  # noqa: E501
    """
    accept = request.headers.get("accept", "")
    return "text/event-stream" in accept.lower()


# ---------------------------------------------------------------------------
# Core /v1 proxy
# ---------------------------------------------------------------------------


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
      StreamingResponse with robust error handling.
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
                    "param": None,
                    "code": None,
                }
            },
        )

    headers = _filter_request_headers(request.headers)
    headers["Authorization"] = f"Bearer {OPENAI_API_KEY}"

    params = dict(request.query_params)
    body = await request.body()

    timeout = httpx.Timeout(PROXY_TIMEOUT)
    is_sse = _is_sse_request(request)

    async with httpx.AsyncClient(base_url=OPENAI_API_BASE, timeout=timeout) as client:
        try:
            if is_sse:
                # SSE: maintain an open connection and forward bytes as they arrive.
                upstream_ctx = client.stream(
                    method,
                    path,
                    params=params,
                    headers=headers,
                    content=body if body else None,
                )
                upstream = await upstream_ctx.__aenter__()

                resp_headers = _filter_response_headers(upstream.headers)
                media_type = upstream.headers.get("content-type", "text/event-stream")

                async def _aiter() -> Any:
                    try:
                        # Use aiter_bytes so httpx handles any content encoding.
                        async for chunk in upstream.aiter_bytes():
                            if chunk:
                                yield chunk
                    except (httpx.ReadError, httpx.HTTPError) as exc:
                        # Treat upstream streaming errors as end-of-stream:
                        # log and stop the iterator instead of crashing the app.
                        logger.warning(
                            "Upstream SSE error (%s %s): %r", method, path, exc
                        )
                    finally:
                        await upstream_ctx.__aexit__(None, None, None)

                return StreamingResponse(
                    _aiter(),
                    status_code=upstream.status_code,
                    headers=resp_headers,
                    media_type=media_type,
                )

            # Non-streaming: single request/response
            upstream_response = await client.request(
                method,
                path,
                params=params,
                headers=headers,
                content=body if body else None,
            )
        except httpx.RequestError as exc:
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


# ---------------------------------------------------------------------------
# Programmatic forwarding for /v1/actions/openai/forward
# ---------------------------------------------------------------------------


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
    Programmatic forwarding used by the Actions router.

    Parameters
    ----------
    method:
        HTTP method, e.g. "GET", "POST".
    path:
        OpenAI-compatible path. Must start with "/v1".
    query:
        Optional query parameters.
    headers:
        Optional additional headers from the caller. Authorization / X-Relay-Key
        are stripped and replaced with relay's credentials.
    body:
        Request body; may be raw bytes/str or JSON-serializable.
    stream:
        If True, create an SSE stream to OpenAI and proxy it to the caller.
    """
    _ensure_api_key()

    if not path.startswith("/v1"):
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "message": "path must start with /v1",
                    "type": "invalid_request_error",
                    "param": None,
                    "code": None,
                }
            },
        )

    method = method.upper()

    base_headers = _filter_request_headers(headers or {})
    base_headers["Authorization"] = f"Bearer {OPENAI_API_KEY}"

    timeout = httpx.Timeout(PROXY_TIMEOUT)
    params = dict(query or {})

    # Normalize body into either JSON or raw content
    json_body: Any = None
    content_body: Optional[Union[str, bytes]] = None

    if isinstance(body, (bytes, str)) or body is None:
        content_body = body
    else:
        json_body = body

    async with httpx.AsyncClient(base_url=OPENAI_API_BASE, timeout=timeout) as client:
        try:
            if stream:
                upstream_ctx = client.stream(
                    method,
                    path,
                    params=params,
                    headers=base_headers,
                    json=json_body,
                    content=content_body,
                )
                upstream = await upstream_ctx.__aenter__()

                resp_headers = _filter_response_headers(upstream.headers)
                media_type = upstream.headers.get("content-type", "text/event-stream")

                async def _aiter() -> Any:
                    try:
                        async for chunk in upstream.aiter_bytes():
                            if chunk:
                                yield chunk
                    except (httpx.ReadError, httpx.HTTPError) as exc:
                        logger.warning(
                            "Upstream SSE error (from_parts %s %s): %r",
                            method,
                            path,
                            exc,
                        )
                    finally:
                        await upstream_ctx.__aexit__(None, None, None)

                return StreamingResponse(
                    _aiter(),
                    status_code=upstream.status_code,
                    headers=resp_headers,
                    media_type=media_type,
                )

            # Non-streaming call
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
