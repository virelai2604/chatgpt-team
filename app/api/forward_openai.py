# app/api/forward_openai.py

from __future__ import annotations

import logging
from typing import Any, Dict, Mapping, Optional, Union, AsyncIterator

import httpx
from fastapi import HTTPException, Request, Response
from fastapi.responses import StreamingResponse

from app.core.config import settings

logger = logging.getLogger("relay")

# ---------------------------------------------------------------------------
# Upstream config
# ---------------------------------------------------------------------------

OPENAI_API_BASE: str = str(settings.OPENAI_API_BASE).rstrip("/")
OPENAI_API_KEY: str = settings.OPENAI_API_KEY
PROXY_TIMEOUT: float = settings.PROXY_TIMEOUT

OPENAI_ASSISTANTS_BETA: str = settings.OPENAI_ASSISTANTS_BETA
OPENAI_REALTIME_BETA: str = settings.OPENAI_REALTIME_BETA

# ---------------------------------------------------------------------------
# Header filtering
# ---------------------------------------------------------------------------

# Headers we never forward to OpenAI
_HOP_BY_HOP_REQUEST_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
    "host",
    # relay-internal
    "x-relay-key",
}

# Headers we strip from OpenAI responses before returning to the client
_HOP_BY_HOP_RESPONSE_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
}


def _filter_request_headers(headers: Mapping[str, str]) -> Dict[str, str]:
    """
    Copy request headers, removing hop‑by‑hop and relay‑internal ones.
    """
    out: Dict[str, str] = {}
    for name, value in headers.items():
        lname = name.lower()
        if lname in _HOP_BY_HOP_REQUEST_HEADERS:
            continue
        # httpx will handle compression
        if lname == "accept-encoding":
            continue
        out[name] = value
    return out


def _filter_response_headers(headers: Mapping[str, str]) -> Dict[str, str]:
    """
    Copy response headers, stripping hop‑by‑hop ones.
    """
    out: Dict[str, str] = {}
    for name, value in headers.items():
        lname = name.lower()
        if lname in _HOP_BY_HOP_RESPONSE_HEADERS:
            continue
        out[name] = value
    return out


def _is_sse_request(request: Request) -> bool:
    """
    Detect Server‑Sent Events (Responses API streaming).

    The official docs and your E2E use `Accept: text/event-stream` for
    Responses streaming. We key off that header. 
    """
    accept = request.headers.get("accept", "")
    return "text/event-stream" in accept.lower()


def _apply_beta_headers(path: str, headers: Dict[str, str]) -> None:
    """
    Attach OpenAI beta headers when hitting beta endpoints. 
    """
    # Assistants / Threads / Runs
    if path.startswith("/v1/assistants") or path.startswith("/v1/threads") or path.startswith("/v1/runs"):
        headers.setdefault("OpenAI-Beta", OPENAI_ASSISTANTS_BETA)

    # Realtime endpoints
    if path.startswith("/v1/realtime"):
        headers.setdefault("OpenAI-Beta", OPENAI_REALTIME_BETA)


def _missing_api_key_error() -> HTTPException:
    return HTTPException(
        status_code=500,
        detail={
            "error": {
                "message": "Relay misconfigured: OPENAI_API_KEY is not set",
                "type": "configuration_error",
                "param": None,
                "code": "missing_openai_api_key",
            }
        },
    )

# ---------------------------------------------------------------------------
# SSE streaming proxy
# ---------------------------------------------------------------------------


async def _stream_sse_to_client(
    method: str,
    url: str,
    *,
    headers: Dict[str, str],
    params: Dict[str, str],
    body: Optional[bytes],
    timeout: Union[float, httpx.Timeout],
) -> StreamingResponse:
    """
    Open an SSE stream to OpenAI and pipe it directly to the client.

    We manage the httpx client + stream lifetime *inside* the async generator
    so that the connection stays open for the duration of the response.
    This avoids the premature-close pattern that leads to httpx.ReadError.
    """

    async def aiter() -> AsyncIterator[bytes]:
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                async with client.stream(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    content=body,
                ) as upstream:
                    async for chunk in upstream.aiter_raw():
                        if chunk:
                            # Pass through raw SSE bytes unchanged (data: ...\n\n)
                            yield chunk
        except httpx.ReadError as exc:
            # Long‑lived SSE connections can end with a low‑level read error;
            # we just log and stop the stream instead of crashing the app.
            logger.warning("Upstream SSE ReadError from %s: %s", url, exc)
        except httpx.HTTPError as exc:
            logger.error("Upstream SSE HTTP error from %s: %s", url, exc)

    # SSE contract: always text/event-stream
    return StreamingResponse(
        aiter(),
        status_code=200,
        media_type="text/event-stream",
    )

# ---------------------------------------------------------------------------
# Main proxy entrypoint
# ---------------------------------------------------------------------------


async def forward_openai_request(
    request: Request,
    *,
    path_override: Optional[str] = None,
) -> Response:
    """
    Generic proxy for all OpenAI‑compatible /v1/* endpoints.

    - Validates path and configuration.
    - Copies relevant headers + injects Authorization and beta headers.
    - For SSE (`Accept: text/event-stream`), uses StreamingResponse + async
      generator to forward bytes from OpenAI.
    - For non‑streaming requests, performs a normal httpx request and
      returns a standard Response with filtered headers.
    """
    if not OPENAI_API_KEY:
        raise _missing_api_key_error()

    method = request.method.upper()
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

    url = OPENAI_API_BASE.rstrip("/") + path

    headers = _filter_request_headers(request.headers)
    headers["Authorization"] = f"Bearer {OPENAI_API_KEY}"

    _apply_beta_headers(path, headers)

    timeout: Union[float, httpx.Timeout] = httpx.Timeout(PROXY_TIMEOUT)

    body = await request.body()
    params: Dict[str, str] = dict(request.query_params)
    is_sse = _is_sse_request(request)

    # Streaming Responses / SSE path
    if is_sse:
        return await _stream_sse_to_client(
            method=method,
            url=url,
            headers=headers,
            params=params,
            body=body,
            timeout=timeout,
        )

    # Non‑streaming path (standard JSON APIs, file uploads, etc.)
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            upstream_response = await client.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                content=body or None,
            )
    except httpx.TimeoutException as exc:
        logger.error("Upstream OpenAI timeout on %s %s: %s", method, url, exc)
        raise HTTPException(
            status_code=504,
            detail={
                "error": {
                    "message": "Upstream OpenAI request timed out",
                    "type": "timeout_error",
                    "param": None,
                    "code": "upstream_timeout",
                    "extra": {"url": url},
                }
            },
        ) from exc
    except httpx.HTTPError as exc:
        logger.error("Upstream OpenAI HTTP error on %s %s: %s", method, url, exc)
        raise HTTPException(
            status_code=502,
            detail={
                "error": {
                    "message": "Error forwarding request to OpenAI",
                    "type": "upstream_request_error",
                    "param": None,
                    "code": "upstream_request_error",
                    "extra": {"exception": str(exc), "url": url},
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
