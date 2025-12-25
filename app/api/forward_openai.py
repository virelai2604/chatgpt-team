from __future__ import annotations

import gzip
import json
import zlib
from typing import Any, Dict, Iterable, Optional, Tuple

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


def _get_timeout_seconds(settings) -> float:
    # Support either PROXY_TIMEOUT_SECONDS or proxy_timeout_seconds naming.
    for name in ("PROXY_TIMEOUT_SECONDS", "proxy_timeout_seconds"):
        if hasattr(settings, name):
            try:
                return float(getattr(settings, name))
            except Exception:
                continue
    return 90.0


def _get_setting(settings, name: str) -> Optional[Any]:
    if hasattr(settings, name):
        return getattr(settings, name)
    lower = name.lower()
    if hasattr(settings, lower):
        return getattr(settings, lower)
    return None


def _openai_base_url(settings) -> str:
    """
    Upstream base for relay forwarding.

    IMPORTANT: Do NOT use OPENAI_BASE_URL here. That env var is commonly used by
    clients to point to a proxy/relay, and using it server-side risks self-calls.
    """
    base = _get_setting(settings, "OPENAI_API_BASE") or _get_setting(settings, "openai_api_base") or _get_setting(settings, "openai_base_url")
    base = str(base or "").strip()
    return base or "https://api.openai.com/v1"


def _join_upstream_url(base: str, path: str) -> str:
    base = base.rstrip("/")
    path = "/" + path.lstrip("/")
    # Avoid /v1/v1 duplication if base already ends with /v1 and path starts with /v1
    if base.endswith("/v1") and path.startswith("/v1/"):
        base = base[: -len("/v1")]
    return base + path


def build_upstream_url(upstream_path: str, *, request: Optional[Request] = None) -> str:
    settings = get_settings()
    url = _join_upstream_url(_openai_base_url(settings), upstream_path)
    if request and request.url.query:
        url = url + "?" + request.url.query
    return url


def _openai_api_key(settings) -> str:
    key = (_get_setting(settings, "OPENAI_API_KEY") or _get_setting(settings, "openai_api_key") or "").strip()
    if not key:
        # Wiring smoke tests should not become a relay 500 due to missing config.
        raise HTTPException(status_code=400, detail="Server missing OPENAI_API_KEY")
    return key


def _decode_content(body: bytes, content_encoding: Optional[str]) -> bytes:
    if not body:
        return body
    if not content_encoding:
        return body
    enc = content_encoding.strip().lower()
    if enc == "gzip":
        return gzip.decompress(body)
    if enc == "deflate":
        try:
            return zlib.decompress(body)
        except zlib.error:
            return zlib.decompress(body, -zlib.MAX_WBITS)
    return body


def build_outbound_headers(
    inbound_headers: Optional[Dict[str, str]] = None,
    *,
    content_type: Optional[str] = None,
    forward_accept: bool = True,
    extra_headers: Optional[Dict[str, str]] = None,
) -> Dict[str, str]:
    """
    Build upstream headers.

    - Removes hop-by-hop headers
    - Replaces Authorization with OpenAI Bearer auth
    - Forces identity encoding to avoid relay-side decompression complexity
    """
    settings = get_settings()
    api_key = _openai_api_key(settings)

    out: Dict[str, str] = {}

    if inbound_headers:
        for k, v in inbound_headers.items():
            lk = k.lower()
            if lk in HOP_BY_HOP_HEADERS:
                continue
            if lk == "authorization":
                continue
            if lk == "accept" and not forward_accept:
                continue
            if lk == "accept-encoding":
                continue
            out[k] = v

    out["Authorization"] = f"Bearer {api_key}"
    out["Accept-Encoding"] = "identity"

    if content_type:
        out["Content-Type"] = content_type

    # Optional org/project headers (supported by OpenAI).
    if getattr(settings, "OPENAI_ORG", ""):
        out["OpenAI-Organization"] = settings.OPENAI_ORG
    if getattr(settings, "OPENAI_PROJECT", ""):
        out["OpenAI-Project"] = settings.OPENAI_PROJECT

    if extra_headers:
        out.update(extra_headers)

    return out


def filter_upstream_headers(upstream_headers: Dict[str, str]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for k, v in upstream_headers.items():
        lk = k.lower()
        if lk in HOP_BY_HOP_HEADERS:
            continue
        if lk == "content-encoding":
            # We force identity upstream; if a gateway still adds encoding, we decode below.
            continue
        if lk == "content-length":
            # Let Starlette compute it for decoded content.
            continue
        out[k] = v
    return out


async def forward_openai_request(
    request: Request,
    *,
    stream: bool = False,
    override_path: Optional[str] = None,
    override_method: Optional[str] = None,
    body: Optional[bytes] = None,
    extra_headers: Optional[Dict[str, str]] = None,
) -> Response:
    """
    Forward the incoming request to OpenAI upstream.

    Used by most route modules that simply proxy /v1/* endpoints.
    """
    settings = get_settings()
    timeout_s = _get_timeout_seconds(settings)

    method = (override_method or request.method).upper()
    upstream_path = override_path or request.url.path
    url = build_upstream_url(upstream_path, request=request)

    if body is None:
        body = await request.body()

    headers = build_outbound_headers(
        dict(request.headers),
        content_type=request.headers.get("content-type"),
        forward_accept=True,
        extra_headers=extra_headers,
    )

    client = get_async_httpx_client(timeout_seconds=timeout_s)
    if stream:
        req = client.build_request(method, url, headers=headers, content=body)
        upstream = await client.send(req, stream=True)
        return StreamingResponse(
            upstream.aiter_raw(),
            status_code=upstream.status_code,
            headers=filter_upstream_headers(dict(upstream.headers)),
            background=BackgroundTask(upstream.aclose),
        )

    upstream = await client.request(method, url, headers=headers, content=body)
    decoded = _decode_content(upstream.content, upstream.headers.get("content-encoding"))
    return Response(
        content=decoded,
        status_code=upstream.status_code,
        headers=filter_upstream_headers(dict(upstream.headers)),
        media_type=upstream.headers.get("content-type"),
    )


async def forward_openai_method_path(
    method: str,
    upstream_path: str,
    request: Request,
    *,
    json_body: Optional[Any] = None,
    content: Optional[bytes] = None,
    extra_headers: Optional[Dict[str, str]] = None,
    stream: bool = False,
) -> Response:
    """
    Forward an explicit (method, path) to upstream. Used by the JSON proxy route.
    """
    settings = get_settings()
    timeout_s = _get_timeout_seconds(settings)
    url = build_upstream_url(upstream_path, request=request)

    headers = build_outbound_headers(
        dict(request.headers),
        content_type="application/json" if json_body is not None else request.headers.get("content-type"),
        forward_accept=True,
        extra_headers=extra_headers,
    )

    body: bytes
    if content is not None:
        body = content
    elif json_body is not None:
        body = json.dumps(json_body).encode("utf-8")
    else:
        body = await request.body()

    client = get_async_httpx_client(timeout_seconds=timeout_s)
    if stream:
        req = client.build_request(method.upper(), url, headers=headers, content=body)
        upstream = await client.send(req, stream=True)
        return StreamingResponse(
            upstream.aiter_raw(),
            status_code=upstream.status_code,
            headers=filter_upstream_headers(dict(upstream.headers)),
            background=BackgroundTask(upstream.aclose),
        )

    upstream = await client.request(method.upper(), url, headers=headers, content=body)
    decoded = _decode_content(upstream.content, upstream.headers.get("content-encoding"))
    return Response(
        content=decoded,
        status_code=upstream.status_code,
        headers=filter_upstream_headers(dict(upstream.headers)),
        media_type=upstream.headers.get("content-type"),
    )


# ---- Compatibility shims (older imports) ----
def _build_outbound_headers(header_items: Iterable[Tuple[str, str]]) -> Dict[str, str]:
    return build_outbound_headers(dict(header_items))


def _filter_response_headers(upstream_headers: Dict[str, str]) -> Dict[str, str]:
    return filter_upstream_headers(upstream_headers)


def _join_upstream_url_compat(base: str, path: str) -> str:
    return _join_upstream_url(base, path)


# Some modules import _join_upstream_url directly.
_join_upstream_url = _join_upstream_url_compat  # type: ignore


# ---- SDK helpers (used by a few legacy routes) ----
# NOTE: Some route snapshots use the OpenAI Python SDK directly (instead of pure httpx forwarding)
# to get typed responses with `model_dump()`. Keep these helpers for compatibility.

async def forward_embeddings_create(body: Dict[str, Any]):
    settings = get_settings()
    _openai_api_key(settings)  # validate (avoid 500s)
    client = get_async_openai_client(timeout_seconds=_get_timeout_seconds(settings))
    return await client.embeddings.create(**body)


async def forward_responses_create(body: Dict[str, Any]):
    settings = get_settings()
    _openai_api_key(settings)  # validate (avoid 500s)
    client = get_async_openai_client(timeout_seconds=_get_timeout_seconds(settings))
    return await client.responses.create(**body)
