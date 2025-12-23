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
    return 120.0


def build_outbound_headers(
    inbound_headers: Mapping[str, str],
    openai_api_key: Optional[str] = None,
    content_type: Optional[str] = None,
    forward_accept: bool = True,
    path_hint: Optional[str] = None,
) -> Dict[str, str]:
    """
    Build headers for upstream OpenAI request.

    - If `openai_api_key` is not provided, it is taken from settings.
    - `path_hint` is accepted for older callers (not required for current behavior).
    """
    _ = path_hint  # retained for compatibility

    s = get_settings()
    api_key = openai_api_key or getattr(s, "openai_api_key", None)
    if not api_key:
        raise HTTPException(status_code=500, detail="Missing OPENAI_API_KEY")

    out = _filter_inbound_headers(inbound_headers)

    if not forward_accept:
        out.pop("Accept", None)

    out["Authorization"] = f"Bearer {api_key}"

    if content_type:
        out["Content-Type"] = content_type

    # Optional OpenAI-Beta flags (safe to include; deduped).
    beta_values = []
    if getattr(s, "openai_assistants_beta", False):
        beta_values.append("assistants=v2")
    if getattr(s, "openai_realtime_beta", False):
        beta_values.append("realtime=v1")

    if beta_values:
        existing = out.get("OpenAI-Beta")
        combined = []
        if existing:
            combined.extend([p.strip() for p in existing.split(",") if p.strip()])
        combined.extend(beta_values)

        seen = set()
        deduped = []
        for item in combined:
            if item in seen:
                continue
            seen.add(item)
            deduped.append(item)

        out["OpenAI-Beta"] = ", ".join(deduped)

    return out


# --- Core forwarders ------------------------------------------------------------------

async def forward_openai_request_to_path(
    request: Request,
    *,
    method_override: Optional[str] = None,
    path_override: Optional[str] = None,
) -> Response:
    """
    Forward an inbound FastAPI request to OpenAI, optionally overriding method/path.
    """
    s = get_settings()
    base_url = getattr(s, "openai_base_url", None) or "https://api.openai.com"
    api_key = getattr(s, "openai_api_key", None)
    if not api_key:
        raise HTTPException(status_code=500, detail="Missing OPENAI_API_KEY")

    method = (method_override or request.method).upper()
    upstream_url = build_upstream_url(request, base_url, path_override=path_override)

    body = await request.body()
    inbound_ct = request.headers.get("content-type")

    headers = build_outbound_headers(
        request.headers,
        openai_api_key=api_key,
        content_type=inbound_ct,
        forward_accept=True,
        path_hint=path_override or request.url.path,
    )

    # If there is a body but the client omitted Content-Type, default to JSON.
    if body and not inbound_ct:
        headers["Content-Type"] = "application/json"

    timeout_s = _get_timeout_seconds(s)
    client = get_async_httpx_client(timeout=timeout_s)

    effective_path = path_override or request.url.path
    if _accepts_sse(request.headers) or _is_sse_path(effective_path):
        async with client.stream(method, upstream_url, headers=headers, content=body) as upstream:
            return StreamingResponse(
                upstream.aiter_bytes(),
                status_code=upstream.status_code,
                headers=_filter_upstream_headers(upstream.headers),
                media_type=upstream.headers.get("content-type"),
            )

    upstream_resp = await client.request(method, upstream_url, headers=headers, content=body)
    return Response(
        content=upstream_resp.content,
        status_code=upstream_resp.status_code,
        headers=_filter_upstream_headers(upstream_resp.headers),
        media_type=upstream_resp.headers.get("content-type"),
    )


async def forward_openai_request(request: Request) -> Response:
    return await forward_openai_request_to_path(request)


async def forward_openai_method_path(
    *args: Any,
    method: Optional[str] = None,
    path: Optional[str] = None,
    query: Optional[Dict[str, Any]] = None,
    json_body: Optional[Any] = None,
    inbound_headers: Optional[Mapping[str, str]] = None,
) -> Response:
    """
    Forward to a specific upstream method/path.

    Supports:
      - Legacy positional: forward_openai_method_path(<method>, <path>, <request>)
      - New keyword-only: forward_openai_method_path(method=..., path=..., query=..., json_body=..., inbound_headers=...)
    """
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
