from __future__ import annotations

import gzip
import json
import zlib
from typing import Any, AsyncIterator, Dict, Mapping, Optional
from urllib.parse import urlencode

import httpx
from fastapi import Request
from fastapi.responses import Response, StreamingResponse

from app.core.config import get_settings
from app.core.http_client import get_async_httpx_client, get_async_openai_client

# ---------------------------------------------------------------------------
# Header handling
# ---------------------------------------------------------------------------

_HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
    "host",
    "content-length",
}

# We strip Content-Encoding because the relay requests identity upstream and/or
# returns decoded bytes. Keeping Content-Encoding while returning identity bytes
# can break downstream clients (e.g., requests json()).
_STRIP_RESPONSE_HEADERS = {
    *_HOP_BY_HOP_HEADERS,
    "content-encoding",
}


def _get_setting(settings: object, *names: str, default=None):
    """Return the first non-empty attribute among several possible setting names."""
    for name in names:
        if hasattr(settings, name):
            val = getattr(settings, name)
            if val is not None and str(val).strip() != "":
                return val
    return default


def _openai_base_url(settings: object) -> str:
    return str(
        _get_setting(
            settings,
            "OPENAI_BASE_URL",
            "OPENAI_API_BASE",
            "openai_base_url",
            "openai_api_base",
            default="https://api.openai.com/v1",
        )
    ).rstrip("/")


def _openai_api_key(settings: object) -> str:
    key = _get_setting(settings, "OPENAI_API_KEY", "openai_api_key", default="")
    if not key:
        raise RuntimeError("OPENAI_API_KEY is not configured.")
    return str(key)


def _join_url(base: str, path: str) -> str:
    base = base.rstrip("/")
    path = "/" + path.lstrip("/")
    # Avoid /v1/v1 duplication
    if base.endswith("/v1") and path.startswith("/v1/"):
        path = path[len("/v1") :]
    return base + path


def _get_timeout_seconds(settings: object) -> float:
    """Compatibility helper used by some route modules."""
    return float(
        _get_setting(
            settings,
            "PROXY_TIMEOUT_SECONDS",
            "proxy_timeout_seconds",
            "PROXY_TIMEOUT",
            "RELAY_TIMEOUT_SECONDS",
            "RELAY_TIMEOUT",
            default=90.0,
        )
    )


def build_upstream_url(
    path: str,
    *,
    request: Optional[Request] = None,
    base_url: Optional[str] = None,
) -> str:
    """
    Build a full upstream OpenAI URL for the given API path.

    - Handles bases with or without `/v1`
    - Preserves the inbound query string when `request` is provided
    """
    s = get_settings()
    base = (base_url or _openai_base_url(s)).rstrip("/")
    url = _join_url(base, path)

    if request is not None and request.url.query:
        url = url + "?" + request.url.query

    return url


def build_outbound_headers(
    *,
    inbound_headers: Mapping[str, str],
    content_type: Optional[str] = None,
    forward_accept: bool = True,
    accept: Optional[str] = None,
    accept_encoding: str = "identity",
    path_hint: Optional[str] = None,  # compatibility; not used
) -> Dict[str, str]:
    """
    Build upstream request headers.

    Key behavior:
      - Never forward client Authorization upstream.
      - Never forward client Accept-Encoding upstream.
      - Force relay's server-side OpenAI API key.
      - Default Accept-Encoding to identity to avoid brotli/br responses that
        some clients cannot decode.
    """
    s = get_settings()

    out: Dict[str, str] = {}

    for k, v in inbound_headers.items():
        lk = k.lower()

        if lk in _HOP_BY_HOP_HEADERS:
            continue
        if lk == "authorization":
            continue
        if lk == "accept-encoding":
            continue

        # We'll set Accept/Content-Type explicitly below.
        if lk == "accept":
            continue
        if lk == "content-type":
            # Preserve multipart boundary etc unless caller overrides.
            if content_type is None:
                out[k] = v
            continue

        out[k] = v

    # Force upstream OpenAI key.
    out["Authorization"] = f"Bearer {_openai_api_key(s)}"

    # Optional org/project/beta headers from config.
    org = _get_setting(s, "OPENAI_ORG", "OPENAI_ORGANIZATION", "openai_organization", default=None)
    if org:
        out["OpenAI-Organization"] = str(org)

    project = _get_setting(s, "OPENAI_PROJECT", "openai_project", default=None)
    if project:
        out["OpenAI-Project"] = str(project)

    beta = _get_setting(s, "OPENAI_BETA", "openai_beta", default=None)
    if beta:
        out["OpenAI-Beta"] = str(beta)

    # Accept header
    if forward_accept:
        inbound_accept = None
        try:
            inbound_accept = inbound_headers.get("accept")  # type: ignore[attr-defined]
        except Exception:
            inbound_accept = None
        out["Accept"] = accept or inbound_accept or "*/*"

    # Critical: avoid br/brotli unless we can guarantee decode support everywhere.
    out["Accept-Encoding"] = accept_encoding

    # Content-Type override (when caller explicitly sets it).
    if content_type is not None and content_type.strip() != "":
        out["Content-Type"] = content_type

    return out


def filter_upstream_headers(up_headers: httpx.Headers) -> Dict[str, str]:
    """Filter upstream response headers to forward back to the client safely."""
    out: Dict[str, str] = {}
    for k, v in up_headers.items():
        lk = k.lower()
        if lk in _STRIP_RESPONSE_HEADERS:
            continue
        out[k] = v
    return out


def _maybe_model_dump(obj: Any) -> Any:
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if hasattr(obj, "dict"):
        return obj.dict()
    return obj


# ---------------------------------------------------------------------------
# Response body hardening (defensive decoding)
# ---------------------------------------------------------------------------

_JSON_FIRST_BYTES = set(b'{["-0123456789tfn')


def _looks_like_json(data: bytes) -> bool:
    if not data:
        return False
    i = 0
    ln = len(data)
    while i < ln and data[i] in b" \t\r\n":
        i += 1
    if i >= ln:
        return False
    return data[i] in _JSON_FIRST_BYTES


def _decode_content_by_encoding(data: bytes, encoding: str) -> bytes:
    """
    Best-effort decode for common HTTP Content-Encoding values.

    Note: In normal operation we request Accept-Encoding: identity upstream and/or rely on httpx to decode.
    This helper exists only as a defensive fallback for misbehaving proxies.
    """
    if not data:
        return data

    # Multiple encodings can be comma-separated; decode in reverse application order.
    encs = [e.strip().lower() for e in (encoding or "").split(",") if e.strip()]
    if not encs:
        return data

    for enc in reversed(encs):
        if enc in {"identity", "none"}:
            continue

        if enc == "gzip":
            try:
                data = gzip.decompress(data)
                continue
            except Exception:
                # Some servers lie and send zlib-wrapped deflate with gzip header.
                try:
                    data = zlib.decompress(data, wbits=16 + zlib.MAX_WBITS)
                    continue
                except Exception:
                    return data

        if enc == "deflate":
            # Try zlib-wrapped first, then raw deflate.
            try:
                data = zlib.decompress(data)
                continue
            except Exception:
                try:
                    data = zlib.decompress(data, wbits=-zlib.MAX_WBITS)
                    continue
                except Exception:
                    return data

        if enc == "br":
            # Optional dependency; only decode if available.
            brotli = None
            try:
                import brotli as brotli_lib  # type: ignore
                brotli = brotli_lib
            except Exception:
                try:
                    import brotlicffi as brotli_lib  # type: ignore
                    brotli = brotli_lib
                except Exception:
                    brotli = None

            if brotli is None:
                return data

            try:
                data = brotli.decompress(data)  # type: ignore[attr-defined]
                continue
            except Exception:
                return data

        # Unknown encoding: bail out.
        return data

    return data


# ---------------------------------------------------------------------------
# Core forwarders
# ---------------------------------------------------------------------------

async def forward_openai_request(request: Request) -> Response:
    """
    Raw HTTP passthrough to the upstream OpenAI API.

    Supports:
      - JSON + multipart requests
      - SSE streaming when upstream returns text/event-stream

    Hardening:
      - Forces Accept-Encoding=identity upstream (avoids brotli responses that
        break some clients / test harnesses).
      - Never raises on upstream non-2xx; returns upstream status + body.
    """
    upstream_url = build_upstream_url(request.url.path, request=request)

    # Preserve inbound Content-Type unless caller wants to override; this keeps
    # multipart boundaries intact.
    headers = build_outbound_headers(
        inbound_headers=request.headers,
        content_type=None,
        forward_accept=True,
        accept_encoding="identity",
    )

    # Only send a body for methods that can carry one.
    body_bytes: Optional[bytes]
    if request.method.upper() in {"GET", "HEAD"}:
        body_bytes = None
    else:
        body_bytes = await request.body()

    timeout_s = _get_timeout_seconds(get_settings())
    client = get_async_httpx_client(timeout=timeout_s)

    upstream_req = client.build_request(
        method=request.method.upper(),
        url=upstream_url,
        headers=headers,
        content=body_bytes,
    )

    upstream = await client.send(upstream_req, stream=True)
    media_type = upstream.headers.get("content-type")

    # SSE streaming
    if media_type and "text/event-stream" in media_type.lower():

        async def gen() -> AsyncIterator[bytes]:
            try:
                async for chunk in upstream.aiter_bytes():
                    yield chunk
            finally:
                await upstream.aclose()

        return StreamingResponse(
            gen(),
            status_code=upstream.status_code,
            headers=filter_upstream_headers(upstream.headers),
            media_type=media_type,
        )

    # Non-SSE: return buffered content (small JSON payloads, errors, etc.)
    try:
        data = await upstream.aread()
    finally:
        await upstream.aclose()

    # Defensive: if upstream still returns encoded bytes (rare), try to decode.
    content_encoding = upstream.headers.get("content-encoding") or ""
    if content_encoding and media_type and "application/json" in media_type.lower():
        if not _looks_like_json(data):
            data = _decode_content_by_encoding(data, content_encoding)

    return Response(
        content=data,
        status_code=upstream.status_code,
        headers=filter_upstream_headers(upstream.headers),
        media_type=media_type,
    )


async def forward_openai_method_path(
    method: str,
    path: str,
    request: Optional[Request] = None,
    *,
    query: Optional[Mapping[str, Any]] = None,
    json_body: Optional[Any] = None,
    body: Optional[Any] = None,
    inbound_headers: Optional[Mapping[str, str]] = None,
) -> Response:
    """
    JSON-focused forwarder used by /v1/proxy and a few compatibility routes.

    Supports multiple call styles that exist in the codebase:
      - forward_openai_method_path("POST", "/v1/videos", request)
      - forward_openai_method_path(method="POST", path="/v1/responses", query=..., json_body=..., inbound_headers=...)
    """
    s = get_settings()
    base_url = _openai_base_url(s)
    url = _join_url(base_url, path)

    if query:
        url = url + "?" + urlencode(query, doseq=True)

    headers_source: Mapping[str, str]
    if inbound_headers is not None:
        headers_source = inbound_headers
    elif request is not None:
        headers_source = request.headers
    else:
        headers_source = {}

    # Prefer json_body, fall back to body for legacy callers.
    payload = json_body if json_body is not None else body

    content: Optional[bytes] = None
    content_type: Optional[str] = None

    m = method.strip().upper()
    if m not in {"GET", "HEAD"}:
        if payload is None:
            content = None
        elif isinstance(payload, (bytes, bytearray)):
            content = bytes(payload)
        else:
            content = json.dumps(payload).encode("utf-8")
            content_type = "application/json"

    headers = build_outbound_headers(
        inbound_headers=headers_source,
        content_type=content_type,
        forward_accept=True,
        accept_encoding="identity",
    )

    timeout_s = _get_timeout_seconds(s)
    client = get_async_httpx_client(timeout=timeout_s)
    upstream = await client.request(m, url, headers=headers, content=content)

    data = upstream.content
    media_type = upstream.headers.get("content-type")
    content_encoding = upstream.headers.get("content-encoding") or ""
    if content_encoding and media_type and "application/json" in media_type.lower():
        if not _looks_like_json(data):
            data = _decode_content_by_encoding(data, content_encoding)

    return Response(
        content=data,
        status_code=upstream.status_code,
        headers=filter_upstream_headers(upstream.headers),
        media_type=media_type,
    )


# ---------------------------------------------------------------------------
# Typed helpers (openai-python SDK)
# ---------------------------------------------------------------------------

async def forward_responses_create(payload: Dict[str, Any]) -> Any:
    """
    Typed helper for non-streaming /v1/responses.

    Some routers import this symbol directly (keep stable).
    """
    client = get_async_openai_client()
    result = await client.responses.create(**payload)
    return _maybe_model_dump(result)


async def forward_embeddings_create(payload: Dict[str, Any]) -> Any:
    client = get_async_openai_client()
    result = await client.embeddings.create(**payload)
    return _maybe_model_dump(result)


__all__ = [
    "_get_timeout_seconds",
    "build_outbound_headers",
    "build_upstream_url",
    "filter_upstream_headers",
    "forward_openai_request",
    "forward_openai_method_path",
    "forward_responses_create",
    "forward_embeddings_create",
]
