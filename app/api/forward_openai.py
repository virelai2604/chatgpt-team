from __future__ import annotations

import re
from typing import Any, Dict, Mapping, Optional

from fastapi import HTTPException, Request
from fastapi.responses import Response, StreamingResponse

from app.core.config import get_settings
from app.core.http_client import get_async_httpx_client

# --- Streaming route detection --------------------------------------------------------

# Include :stream variants used by some OpenAI endpoints.
_SSE_PATH_RE = re.compile(r"^/v1/(responses(?::stream)?|chat/completions(?::stream)?)$")


def _is_sse_path(path: str) -> bool:
    return _SSE_PATH_RE.match(path) is not None


def _accepts_sse(headers: Mapping[str, str]) -> bool:
    accept = headers.get("accept", "") or headers.get("Accept", "")
    return "text/event-stream" in accept.lower()


# --- Header/url helpers ---------------------------------------------------------------

def _join_url(base: str, path: str) -> str:
    return f"{base.rstrip('/')}/{path.lstrip('/')}"


def _filter_inbound_headers(headers: Mapping[str, str]) -> Dict[str, str]:
    """
    Remove hop-by-hop and unsafe headers before proxying upstream.
    """
    out: Dict[str, str] = {}
    for k, v in headers.items():
        lk = k.lower()
        if lk in {"host", "connection", "content-length"}:
            continue
        if lk.startswith("sec-") or lk in {
            "upgrade",
            "keep-alive",
            "proxy-authenticate",
            "proxy-authorization",
            "te",
            "trailer",
            "transfer-encoding",
        }:
            continue
        out[k] = v
    return out


def _filter_upstream_headers(headers: Mapping[str, str]) -> Dict[str, str]:
    """
    Remove hop-by-hop/encoding headers from upstream response.
    """
    out: Dict[str, str] = {}
    for k, v in headers.items():
        lk = k.lower()
        if lk in {"content-encoding", "transfer-encoding", "connection"}:
            continue
        out[k] = v
    return out


# Back-compat alias used by some route modules.
def filter_upstream_headers(headers: Mapping[str, str]) -> Dict[str, str]:
    return _filter_upstream_headers(headers)


def build_upstream_url(*args: Any, **kwargs: Any) -> str:
    """
    Backwards-compatible URL builder.

    Supported call styles:
      1) New style:
           build_upstream_url(request, base_url, path_override="/v1/...")
      2) Legacy style:
           build_upstream_url("/v1/...", request=request, base_url="https://api.openai.com")
           build_upstream_url("/v1/...")
    """
    # New style: (request, base_url, path_override=...)
    if len(args) >= 2 and isinstance(args[0], Request) and isinstance(args[1], str):
        request: Request = args[0]
        base_url: str = args[1]
        path_override: Optional[str] = kwargs.get("path_override")
        path = path_override or request.url.path
        url = _join_url(base_url, path)
        if request.url.query:
            url = f"{url}?{request.url.query}"
        return url

    # Legacy style: (path, ...)
    if len(args) >= 1 and isinstance(args[0], str):
        path: str = args[0]
        request: Optional[Request] = kwargs.get("request")
        base_url: Optional[str] = kwargs.get("base_url")

        s = get_settings()
        base = base_url or getattr(s, "openai_base_url", None) or "https://api.openai.com"

        url = _join_url(base, path)
        if request is not None and request.url.query:
            url = f"{url}?{request.url.query}"
        return url

    raise TypeError("build_upstream_url() received unsupported arguments")


def _get_timeout_seconds(settings: Optional[Any] = None) -> float:
    """
    Back-compat: support multiple config field names and legacy call sites that
    invoke _get_timeout_seconds() with no args.
    """
    s = settings or get_settings()
    for name in ("proxy_timeout_seconds", "proxy_timeout", "proxy_timeout_s"):
        if hasattr(s, name):
            try:
                return float(getattr(s, name))
            except Exception:
                pass
    # Conservative fallback.
    return 90.0


def build_outbound_headers(
    inbound_headers: Mapping[str, str],
    *,
    openai_api_key: Optional[str] = None,
    content_type: Optional[str] = "application/json",
    forward_accept: bool = True,
    path_hint: Optional[str] = None,
) -> Dict[str, str]:
    """
    Build outbound headers for upstream OpenAI requests.

    - Copies safe inbound headers
    - Forces Authorization: Bearer <OPENAI_API_KEY>
    - Optionally sets Content-Type
    - Preserves Accept if requested
    """
    s = get_settings()
    api_key = openai_api_key or getattr(s, "openai_api_key", None)
    if not api_key:
        raise HTTPException(status_code=500, detail="Missing OPENAI_API_KEY")

    out = _filter_inbound_headers(inbound_headers)

    # Overwrite auth to ensure relay uses server-side key.
    out["Authorization"] = f"Bearer {api_key}"

    # Optional organization/project headers if present.
    org = getattr(s, "openai_organization", None)
    proj = getattr(s, "openai_project", None)
    if org:
        out["OpenAI-Organization"] = str(org)
    if proj:
        out["OpenAI-Project"] = str(proj)

    # Optional beta flags (if configured).
    beta = getattr(s, "openai_beta", None)
    if beta:
        out["OpenAI-Beta"] = str(beta)

    # Content-Type handling:
    # - For JSON routes we set application/json
    # - For multipart routes caller should pass content_type=None
    if content_type is not None:
        out["Content-Type"] = content_type
    else:
        out.pop("Content-Type", None)

    if not forward_accept:
        # Some upstream routes are happier without Accept forwarding.
        out.pop("Accept", None)

    # Route-specific hinting (no-op unless you later need special cases).
    _ = path_hint

    return out


async def forward_openai_request(request: Request) -> Response:
    """
    Forward the inbound Request to OpenAI upstream.

    - Detects SSE routes and streams bytes without buffering
    - Otherwise returns a buffered Response with upstream headers filtered
    """
    s = get_settings()
    base_url = getattr(s, "openai_base_url", None) or "https://api.openai.com"
    api_key = getattr(s, "openai_api_key", None)
    if not api_key:
        raise HTTPException(status_code=500, detail="Missing OPENAI_API_KEY")

    upstream_url = build_upstream_url(request, base_url)

    headers = build_outbound_headers(
        request.headers,
        openai_api_key=api_key,
        content_type=request.headers.get("content-type"),
        forward_accept=True,
        path_hint=request.url.path,
    )

    timeout_s = _get_timeout_seconds(s)
    client = get_async_httpx_client(timeout=timeout_s)

    method = request.method.upper()

    # Streaming detection: either explicit SSE endpoint or Accept header indicates SSE
    if _is_sse_path(request.url.path) or _accepts_sse(request.headers):
        body = await request.body()
        upstream = await client.stream(method, upstream_url, headers=headers, content=body)

        async def _iter_bytes():
            async with upstream:
                async for chunk in upstream.aiter_bytes():
                    yield chunk

        return StreamingResponse(
            _iter_bytes(),
            status_code=upstream.status_code,
            headers=_filter_upstream_headers(upstream.headers),
            media_type=upstream.headers.get("content-type"),
        )

    body = await request.body()
    resp = await client.request(method, upstream_url, headers=headers, content=body)

    return Response(
        content=resp.content,
        status_code=resp.status_code,
        headers=_filter_upstream_headers(resp.headers),
        media_type=resp.headers.get("content-type"),
    )


async def forward_openai_request_to_path(
    request: Request,
    *,
    method_override: Optional[str] = None,
    path_override: Optional[str] = None,
) -> Response:
    """
    Forward request to a different method and/or path than the inbound request.
    """
    s = get_settings()
    base_url = getattr(s, "openai_base_url", None) or "https://api.openai.com"
    api_key = getattr(s, "openai_api_key", None)
    if not api_key:
        raise HTTPException(status_code=500, detail="Missing OPENAI_API_KEY")

    method = (method_override or request.method).upper()
    upstream_path = path_override or request.url.path
    upstream_url = build_upstream_url(request, base_url, path_override=upstream_path)

    headers = build_outbound_headers(
        request.headers,
        openai_api_key=api_key,
        content_type=request.headers.get("content-type"),
        forward_accept=True,
        path_hint=upstream_path,
    )

    timeout_s = _get_timeout_seconds(s)
    client = get_async_httpx_client(timeout=timeout_s)

    # Preserve body
    body = await request.body()

    # SSE handling for override paths too
    if _is_sse_path(upstream_path) or _accepts_sse(request.headers):
        upstream = await client.stream(method, upstream_url, headers=headers, content=body)

        async def _iter_bytes():
            async with upstream:
                async for chunk in upstream.aiter_bytes():
                    yield chunk

        return StreamingResponse(
            _iter_bytes(),
            status_code=upstream.status_code,
            headers=_filter_upstream_headers(upstream.headers),
            media_type=upstream.headers.get("content-type"),
        )

    resp = await client.request(method, upstream_url, headers=headers, content=body)
    return Response(
        content=resp.content,
        status_code=resp.status_code,
        headers=_filter_upstream_headers(resp.headers),
        media_type=resp.headers.get("content-type"),
    )


async def forward_openai_method_path(*args: Any, **kwargs: Any) -> Response:
    """
    Forward to a specific upstream method/path.

    Supports:
      - Legacy positional: forward_openai_method_path(<method>, <path>, <request>)
      - New keyword-only: forward_openai_method_path(method=..., path=..., query=..., json_body=..., inbound_headers=...)
    """
    method: Optional[str] = kwargs.pop("method", None)
    path: Optional[str] = kwargs.pop("path", None)
    query: Optional[Dict[str, Any]] = kwargs.pop("query", None)
    json_body: Optional[Any] = kwargs.pop("json_body", None)
    inbound_headers: Optional[Mapping[str, str]] = kwargs.pop("inbound_headers", None)

    # Legacy style: (method, path, request)
    if (
        len(args) >= 3
        and isinstance(args[0], str)
        and isinstance(args[1], str)
        and isinstance(args[2], Request)
    ):
        legacy_method: str = args[0]
        legacy_path: str = args[1]
        legacy_request: Request = args[2]
        return await forward_openai_request_to_path(
            legacy_request,
            method_override=legacy_method,
            path_override=legacy_path,
        )

    if args:
        raise TypeError("forward_openai_method_path() received unexpected positional arguments")

    if not method or not path:
        raise TypeError("forward_openai_method_path() missing required 'method' and/or 'path'")

    s = get_settings()
    base_url = getattr(s, "openai_base_url", None) or "https://api.openai.com"
    api_key = getattr(s, "openai_api_key", None)
    if not api_key:
        raise HTTPException(status_code=500, detail="Missing OPENAI_API_KEY")

    url = _join_url(base_url, path)
    headers = build_outbound_headers(
        inbound_headers or {},
        openai_api_key=api_key,
        content_type="application/json",
        forward_accept=True,
        path_hint=path,
    )

    timeout_s = _get_timeout_seconds(s)
    client = get_async_httpx_client(timeout=timeout_s)

    resp = await client.request(method.upper(), url, params=query, json=json_body, headers=headers)
    return Response(
        content=resp.content,
        status_code=resp.status_code,
        headers=_filter_upstream_headers(resp.headers),
        media_type=resp.headers.get("content-type"),
    )


async def forward_embeddings_create(body: Any) -> Dict[str, Any]:
    """
    Used by app.routes.embeddings. Returns the upstream JSON payload.
    """
    s = get_settings()
    base_url = getattr(s, "openai_base_url", None) or "https://api.openai.com"
    api_key = getattr(s, "openai_api_key", None)
    if not api_key:
        raise HTTPException(status_code=500, detail="Missing OPENAI_API_KEY")

    url = _join_url(base_url, "/v1/embeddings")
    headers = build_outbound_headers(
        {},
        openai_api_key=api_key,
        content_type="application/json",
        forward_accept=False,
        path_hint="/v1/embeddings",
    )

    timeout_s = _get_timeout_seconds(s)
    client = get_async_httpx_client(timeout=timeout_s)

    resp = await client.post(url, json=body, headers=headers)
    try:
        payload = resp.json()
    except Exception:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)

    if resp.status_code >= 400:
        # Preserve upstream error structure.
        raise HTTPException(status_code=resp.status_code, detail=payload)

    if not isinstance(payload, dict):
        raise HTTPException(status_code=502, detail="Upstream returned non-object JSON for embeddings")
    return payload
