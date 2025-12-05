# app/api/forward_openai.py

from __future__ import annotations

import json
import logging
from typing import Any, AsyncIterator, Dict, Mapping, Optional

import httpx
from fastapi import HTTPException, Request
from fastapi.responses import Response, StreamingResponse

from app.core.config import settings

logger = logging.getLogger("relay.forward_openai")

# Normalised configuration
OPENAI_API_BASE = str(settings.OPENAI_API_BASE).rstrip("/")
OPENAI_API_KEY = settings.OPENAI_API_KEY
PROXY_TIMEOUT = float(getattr(settings, "PROXY_TIMEOUT", 120.0) or 120.0)

# Hop‑by‑hop headers that must not be forwarded
HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
}

# Additional request headers we always strip from the client
STRIP_REQUEST_HEADERS = {
    "host",
    "authorization",
    "content-length",
    "accept-encoding",
    "x-forwarded-for",
    "x-forwarded-host",
    "x-forwarded-proto",
}

# Response headers to drop; ASGI stack recomputes these
STRIP_RESPONSE_HEADERS = {
    "transfer-encoding",
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailer",
    "upgrade",
}


def _ensure_api_key() -> None:
    """Ensure the relay has an upstream OpenAI API key configured."""
    if not OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY is not configured on the relay.")
        raise HTTPException(
            status_code=500,
            detail="Relay misconfigured: OPENAI_API_KEY is not set.",
        )


def _build_full_url(path: str) -> str:
    """
    Combine OPENAI_API_BASE and the requested path, making sure `/v1`
    is present exactly once.

    - If base already ends with `/v1` and path starts with `/v1/`, drop
      the duplicated `/v1` from the path.
    - If base does not end with `/v1` and path does not start with `/v1/`,
      prefix `/v1`.
    """
    if not path.startswith("/"):
        path = "/" + path

    base = OPENAI_API_BASE.rstrip("/")

    if base.endswith("/v1"):
        if path.startswith("/v1/"):
            # remove leading "/v1"
            path = path[3:]
    else:
        if not path.startswith("/v1/"):
            path = "/v1" + path

    return f"{base}{path}"


def _filter_request_headers(headers: Mapping[str, str]) -> Dict[str, str]:
    """
    Drop hop‑by‑hop headers, client Authorization, and any OpenAI‑specific
    headers. The relay injects its own OpenAI credentials.
    """
    filtered: Dict[str, str] = {}
    for name, value in headers.items():
        key = name.lower()
        if key in HOP_BY_HOP_HEADERS:
            continue
        if key in STRIP_REQUEST_HEADERS:
            continue
        # prevent clients from smuggling their own OpenAI headers
        if key.startswith("openai-") or key.startswith("x-openai-"):
            continue
        filtered[name] = value
    return filtered


def _filter_response_headers(headers: Mapping[str, str]) -> Dict[str, str]:
    """
    Drop hop‑by‑hop headers and Content-Length from upstream responses.
    """
    filtered: Dict[str, str] = {}
    for name, value in headers.items():
        key = name.lower()
        if key in HOP_BY_HOP_HEADERS or key in STRIP_RESPONSE_HEADERS:
            continue
        if key == "content-length":
            continue
        filtered[name] = value
    return filtered


def _build_upstream_headers(
    incoming: Mapping[str, str],
    *,
    is_stream: bool,
) -> Dict[str, str]:
    """
    Start from filtered client headers and inject OpenAI auth + sane
    defaults for Accept / encoding.
    """
    _ensure_api_key()

    headers: Dict[str, str] = dict(incoming)

    # Relay owns the OpenAI API key
    headers["Authorization"] = f"Bearer {OPENAI_API_KEY}"

    # Accept type depends on streaming vs JSON
    if is_stream:
        headers["Accept"] = "text/event-stream"
    else:
        headers.setdefault("Accept", "application/json")

    # Avoid gzip – we stream raw bytes through the ASGI stack.
    headers["Accept-Encoding"] = "identity"

    return headers


def _parse_request_body(
    content_type: str,
    body_bytes: bytes,
) -> tuple[Optional[Any], Optional[bytes]]:
    """
    Return (json_body, raw_body). Only one of them will be non‑None.
    """
    if not body_bytes:
        # Empty body – treat as empty bytes
        return None, b""

    main_type = (
        content_type.split(";", 1)[0].strip().lower() if content_type else ""
    )

    if main_type == "application/json":
        try:
            data = json.loads(body_bytes.decode("utf-8"))
        except json.JSONDecodeError:
            # Pass through unparsed if client sent broken JSON
            return None, body_bytes
        else:
            return data, None

    # Everything else: treat as raw bytes (e.g. multipart)
    return None, body_bytes


async def _do_forward(
    *,
    method: str,
    path: str,
    headers: Mapping[str, str],
    query_params: Optional[Mapping[str, Any]],
    json_body: Optional[Any],
    raw_body: Optional[bytes],
) -> Response:
    """
    Perform a non‑streaming HTTP request to the OpenAI API.
    """
    url = _build_full_url(path)
    timeout = PROXY_TIMEOUT

    try:
        async with httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=False,
        ) as client:
            resp = await client.request(
                method=method,
                url=url,
                params=dict(query_params or {}),
                headers=headers,
                json=json_body if json_body is not None else None,
                content=None if json_body is not None else raw_body,
            )
    except httpx.RequestError as exc:
        logger.exception(
            "Error proxying OpenAI request %s %s: %s", method, url, exc
        )
        raise HTTPException(
            status_code=502,
            detail="Upstream OpenAI API request failed.",
        ) from exc

    return Response(
        content=resp.content,
        status_code=resp.status_code,
        headers=_filter_response_headers(resp.headers),
        media_type=resp.headers.get("content-type"),
    )


async def _do_forward_streaming(
    *,
    method: str,
    path: str,
    headers: Mapping[str, str],
    query_params: Optional[Mapping[str, Any]],
    json_body: Optional[Any],
    raw_body: Optional[bytes],
) -> StreamingResponse:
    """
    Perform a streaming (SSE) HTTP request to the OpenAI API and stream
    raw bytes back to the client.
    """
    url = _build_full_url(path)
    timeout = PROXY_TIMEOUT

    async def event_generator() -> AsyncIterator[bytes]:
        try:
            async with httpx.AsyncClient(
                timeout=timeout,
                follow_redirects=False,
            ) as client:
                async with client.stream(
                    method=method,
                    url=url,
                    params=dict(query_params or {}),
                    headers=headers,
                    json=json_body if json_body is not None else None,
                    content=None if json_body is not None else raw_body,
                ) as upstream:
                    async for chunk in upstream.aiter_bytes():
                        if not chunk:
                            continue
                        yield chunk
        except httpx.RequestError as exc:
            logger.exception(
                "Error proxying OpenAI streaming request %s %s: %s",
                method,
                url,
                exc,
            )
            # Cannot change status code here – emit a final SSE error event.
            error_payload = {
                "error": {
                    "message": "Upstream OpenAI streaming request failed.",
                    "type": "upstream_error",
                }
            }
            msg = f"event: error\ndata: {json.dumps(error_payload)}\n\n"
            yield msg.encode("utf-8")

    return StreamingResponse(event_generator(), media_type="text/event-stream")


async def forward_openai_request(
    request: Request,
    *,
    method: Optional[str] = None,
    path_override: Optional[str] = None,
) -> Response:
    """
    Generic proxy used by typed `/v1/*` routes.

    - Preserves method, path, and query parameters.
    - Normalises headers and injects relay OpenAI credentials.
    - Handles SSE streaming for `/v1/responses` (and any request that
      asks for `text/event-stream` or has `stream: true` in JSON body).
    """
    _ensure_api_key()

    resolved_method = (method or request.method).upper()
    path = path_override or request.url.path
    query_params = dict(request.query_params)

    incoming_headers = _filter_request_headers(request.headers)
    content_type = request.headers.get("content-type", "")

    body_bytes = await request.body()
    json_body, raw_body = _parse_request_body(content_type, body_bytes)

    # Determine streaming requirements
    wants_stream = False
    accept_header = request.headers.get("accept", "")

    if "text/event-stream" in accept_header.lower():
        wants_stream = True

    if not wants_stream and isinstance(json_body, dict):
        if json_body.get("stream") is True:
            wants_stream = True

    enable_stream = bool(getattr(settings, "ENABLE_STREAM", True))
    is_stream = bool(wants_stream and enable_stream)

    upstream_headers = _build_upstream_headers(
        incoming_headers,
        is_stream=is_stream,
    )

    if is_stream:
        return await _do_forward_streaming(
            method=resolved_method,
            path=path,
            headers=upstream_headers,
            query_params=query_params,
            json_body=json_body,
            raw_body=raw_body,
        )

    return await _do_forward(
        method=resolved_method,
        path=path,
        headers=upstream_headers,
        query_params=query_params,
        json_body=json_body,
        raw_body=raw_body,
    )


async def forward_openai_from_parts(
    *,
    method: str,
    path: str,
    query: Optional[Mapping[str, Any]] = None,
    body: Optional[Any] = None,
    headers: Optional[Mapping[str, str]] = None,
) -> Response:
    """
    Programmatic proxy used by `/v1/actions/openai/forward`.

    Accepts decomposed request parts instead of a FastAPI `Request`.
    This path is non‑streaming: callers receive the final JSON / HTTP
    response body from OpenAI.
    """
    _ensure_api_key()

    resolved_method = method.upper()
    query_params = dict(query or {})

    incoming_headers = _filter_request_headers(headers or {})

    json_body: Optional[Any] = None
    raw_body: Optional[bytes]

    if body is None:
        raw_body = b""
    elif isinstance(body, (dict, list)):
        json_body = body
        raw_body = None
    elif isinstance(body, bytes):
        raw_body = body
    elif isinstance(body, str):
        raw_body = body.encode("utf-8")
    else:
        raise HTTPException(
            status_code=422,
            detail="Unsupported body type for OpenAI forward action.",
        )

    upstream_headers = _build_upstream_headers(
        incoming_headers,
        is_stream=False,
    )

    return await _do_forward(
        method=resolved_method,
        path=path,
        headers=upstream_headers,
        query_params=query_params,
        json_body=json_body,
        raw_body=raw_body,
    )


__all__ = [
    "forward_openai_request",
    "forward_openai_from_parts",
]
