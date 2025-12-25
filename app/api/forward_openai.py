from __future__ import annotations

import gzip
import json
import zlib
from typing import Any, Dict, Optional, Union
from urllib.parse import urlencode

import httpx
from fastapi import HTTPException, Request
from starlette.background import BackgroundTask
from starlette.responses import Response, StreamingResponse

from app.core.config import get_settings
from app.core.http_client import get_async_httpx_client, get_async_openai_client


HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
    "host",
    "content-length",
}

_DEFAULT_JSON_CT = "application/json"


def _get_setting(settings: object, *names: str, default: Optional[object] = None) -> Optional[object]:
    for n in names:
        if hasattr(settings, n):
            v = getattr(settings, n)
            if v is not None:
                return v
        ln = n.lower()
        if hasattr(settings, ln):
            v = getattr(settings, ln)
            if v is not None:
                return v
    return default


def _get_timeout_seconds(settings: object) -> float:
    v = _get_setting(settings, "PROXY_TIMEOUT_SECONDS", "proxy_timeout_seconds", default=90.0)
    try:
        return float(v)  # type: ignore[arg-type]
    except Exception:
        return 90.0


def _openai_base_url(settings: object) -> str:
    """
    Upstream base for relay forwarding.

    IMPORTANT: Do NOT use OPENAI_BASE_URL here. That env var is commonly used by
    clients to point to a proxy/relay; using it server-side risks self-calls.
    """
    base = _get_setting(settings, "OPENAI_API_BASE", "openai_api_base", "openai_base_url", default="https://api.openai.com/v1")
    base = str(base or "").strip()
    return base or "https://api.openai.com/v1"


def _openai_api_key(settings: object) -> str:
    key = _get_setting(settings, "OPENAI_API_KEY", "openai_api_key", default="")
    if not key:
        # Avoid turning wiring errors into 5xx; treat as a client-visible config issue.
        raise HTTPException(status_code=400, detail="Server missing OPENAI_API_KEY")
    return str(key)


def _join_url(base: str, path: str) -> str:
    base = base.rstrip("/")
    path = "/" + path.lstrip("/")
    # Avoid /v1/v1 duplication if base already ends with /v1 and path starts with /v1
    if base.endswith("/v1") and path.startswith("/v1/"):
        base = base[: -len("/v1")]
    return base + path


def build_upstream_url(
    upstream_path: str,
    request: Optional[Request] = None,
    *,
    base_url: Optional[str] = None,
    query_params: Optional[Dict[str, str]] = None,
) -> str:
    settings = get_settings()
    base = base_url or _openai_base_url(settings)
    url = _join_url(base, upstream_path)

    qp: Dict[str, str] = {}
    if request is not None:
        qp.update(dict(request.query_params))
    if query_params:
        qp.update({k: v for k, v in query_params.items() if v is not None})
    if qp:
        url = url + "?" + urlencode(qp, doseq=True)
    return url


def build_outbound_headers(
    inbound_headers: Dict[str, str],
    *,
    content_type: Optional[str] = None,
    accept: Optional[str] = None,
    forward_accept: bool = True,
    accept_encoding: Optional[str] = None,
    extra_headers: Optional[Dict[str, str]] = None,
) -> Dict[str, str]:
    """
    Build upstream headers.

    - Removes hop-by-hop headers
    - Replaces Authorization with Bearer <OPENAI_API_KEY>
    - Forces Accept-Encoding to identity (avoid relay gzip edge-cases)
    """
    settings = get_settings()
    api_key = _openai_api_key(settings)

    out: Dict[str, str] = {}
    for k, v in inbound_headers.items():
        lk = k.lower()
        if lk in HOP_BY_HOP_HEADERS:
            continue
        if lk == "authorization":
            continue
        if lk == "accept-encoding":
            continue
        if not forward_accept and lk == "accept":
            continue
        out[k] = v

    out["Authorization"] = f"Bearer {api_key}"

    if accept is not None:
        out["Accept"] = accept
    elif forward_accept and "Accept" not in out:
        out["Accept"] = "application/json"

    if content_type is not None:
        out["Content-Type"] = content_type
    elif "Content-Type" not in out:
        # For typical JSON-forwarded routes.
        out["Content-Type"] = _DEFAULT_JSON_CT

    out["Accept-Encoding"] = accept_encoding or "identity"

    if settings.OPENAI_ORG:
        out["OpenAI-Organization"] = settings.OPENAI_ORG
    if settings.OPENAI_PROJECT:
        out["OpenAI-Project"] = settings.OPENAI_PROJECT

    if extra_headers:
        out.update(extra_headers)

    return out


def filter_upstream_headers(upstream_headers: httpx.Headers) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for k, v in upstream_headers.items():
        lk = k.lower()
        if lk in HOP_BY_HOP_HEADERS:
            continue
        out[k] = v
    return out


def _maybe_decompress(content: bytes, encoding: Optional[str]) -> bytes:
    if not encoding:
        return content
    enc = encoding.lower().strip()
    if enc == "gzip":
        return gzip.decompress(content)
    if enc == "deflate":
        return zlib.decompress(content)
    return content


async def forward_openai_request(
    request: Request,
    *,
    method: str,
    upstream_path: str,
    body: Optional[Union[bytes, str, Dict[str, Any]]] = None,
    content_type: Optional[str] = None,
    accept: Optional[str] = None,
    stream: bool = False,
    extra_headers: Optional[Dict[str, str]] = None,
) -> Response:
    settings = get_settings()
    timeout_s = _get_timeout_seconds(settings)

    url = build_upstream_url(upstream_path, request)

    inbound_headers = dict(request.headers)
    headers = build_outbound_headers(
        inbound_headers,
        content_type=content_type,
        accept=accept,
        forward_accept=True,
        accept_encoding="identity",
        extra_headers=extra_headers,
    )

    if body is None:
        raw = await request.body()
    elif isinstance(body, bytes):
        raw = body
    elif isinstance(body, str):
        raw = body.encode("utf-8")
    else:
        raw = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = _DEFAULT_JSON_CT

    client = get_async_httpx_client(timeout=timeout_s)

    if stream:
        req = client.build_request(method.upper(), url, headers=headers, content=raw)
        upstream = await client.send(req, stream=True)
        return StreamingResponse(
            upstream.aiter_raw(),
            status_code=upstream.status_code,
            headers=filter_upstream_headers(upstream.headers),
            background=BackgroundTask(upstream.aclose),
        )

    upstream = await client.request(method.upper(), url, headers=headers, content=raw)

    content = upstream.content
    content = _maybe_decompress(content, upstream.headers.get("content-encoding"))

    return Response(
        content=content,
        status_code=upstream.status_code,
        headers=filter_upstream_headers(upstream.headers),
        media_type=upstream.headers.get("content-type"),
    )


async def forward_openai_method_path(
    method: str,
    upstream_path: str,
    request: Request,
    *,
    body: Optional[bytes] = None,
    content_type: Optional[str] = None,
    accept: Optional[str] = None,
    stream: bool = False,
    extra_headers: Optional[Dict[str, str]] = None,
) -> Response:
    if body is None:
        body = await request.body()

    return await forward_openai_request(
        request,
        method=method,
        upstream_path=upstream_path,
        body=body,
        content_type=content_type,
        accept=accept,
        stream=stream,
        extra_headers=extra_headers,
    )


# ---------------------------------------------------------------------------
# Compatibility shims (used by app.api.sse and some older routes)
# ---------------------------------------------------------------------------

def _build_outbound_headers(inbound_items):
    """Legacy helper expected by app.api.sse.

    Accepts an iterable of (header_name, header_value) pairs.
    """
    return build_outbound_headers(
        inbound_headers=dict(inbound_items),
        # Do not override multipart boundaries; SSE sets Accept downstream.
        forward_accept=False,
        accept_encoding="identity",
    )


def _filter_response_headers(headers: httpx.Headers) -> Dict[str, str]:
    """Legacy helper: filter hop-by-hop headers from an upstream response."""
    return filter_upstream_headers(headers)


def _join_upstream_url(base: str, path: str, query: str = "") -> str:
    """Legacy helper expected by app.api.sse.

    Parameters:
      - base: upstream base (often already ends with /v1)
      - path: upstream path (may start with /v1)
      - query: raw query string without leading '?'
    """
    url = _join_url(base, path)
    query = (query or "").lstrip("?")
    if query:
        url = url + "?" + query
    return url


__all__ = [
    "HOP_BY_HOP_HEADERS",
    "_get_setting",
    "_get_timeout_seconds",
    "build_outbound_headers",
    "filter_upstream_headers",
    "build_upstream_url",
    "_build_outbound_headers",
    "_filter_response_headers",
    "_join_upstream_url",
    "forward_openai_request",
    "forward_openai_method_path",
]
