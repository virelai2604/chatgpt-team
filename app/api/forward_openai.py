from __future__ import annotations

import re
from typing import Any, Dict, Mapping, Optional

import httpx
from fastapi import HTTPException, Request
from fastapi.responses import Response, StreamingResponse

from app.core.config import get_settings
from app.http_client import get_async_httpx_client


# --- Streaming route detection --------------------------------------------------------

_SSE_PATH_RE = re.compile(r"^/v1/(responses|chat/completions)$")


def _is_sse_path(path: str) -> bool:
    """Return True if an upstream route is expected to stream via SSE."""
    return _SSE_PATH_RE.match(path) is not None


# --- Header/url helpers ---------------------------------------------------------------

def _join_url(base: str, path: str) -> str:
    return f"{base.rstrip('/')}/{path.lstrip('/')}"


def _filter_inbound_headers(headers: Mapping[str, str]) -> Dict[str, str]:
    """Remove hop-by-hop and unsafe headers before proxying upstream."""
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
    """Remove hop-by-hop/encoding headers from upstream response."""
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


def build_upstream_url(request: Request, base_url: str, *, path_override: Optional[str] = None) -> str:
    """Build the upstream URL, preserving the original query string."""
    path = path_override or request.url.path
    url = _join_url(base_url, path)
    if request.url.query:
        url = f"{url}?{request.url.query}"
    return url


def _get_timeout_seconds(settings: Any) -> float:
    """Back-compat: support multiple config field names."""
    for name in ("proxy_timeout_seconds", "proxy_timeout", "proxy_timeout_s"):
        if hasattr(settings, name):
            try:
                return float(getattr(settings, name))
            except Exception:
                pass
    return 120.0


def build_outbound_headers(
    inbound_headers: Mapping[str, str],
    openai_api_key: str,
    content_type: Optional[str] = None,
    forward_accept: bool = True,
    path_hint: Optional[str] = None,
) -> Dict[str, str]:
    """
    Create upstream request headers.

    This function intentionally accepts legacy parameters (forward_accept, path_hint)
    so older route modules can call it without raising TypeError.
    """
    # forward_accept/path_hint are retained for compatibility; current implementation
    # always forwards the inbound Accept header if present.
    _ = forward_accept
    _ = path_hint

    out = _filter_inbound_headers(inbound_headers)
    out["Authorization"] = f"Bearer {openai_api_key}"

    if content_type:
        out["Content-Type"] = content_type

    # OpenAI-Beta header can contain multiple comma-separated flags.
    s = get_settings()
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
    """Forward the inbound FastAPI request to OpenAI, optionally overriding method/path."""
    s = get_settings()
    base_url = getattr(s, "openai_base_url", None) or "https://api.openai.com"
    api_key = getattr(s, "openai_api_key", None)
    if not api_key:
        raise HTTPException(status_code=500, detail="Missing OPENAI_API_KEY")

    method = (method_override or request.method).upper()
    upstream_url = build_upstream_url(request, base_url, path_override=path_override)

    body = await request.body()
    headers = build_outbound_headers(
        request.headers,
        api_key,
        content_type=request.headers.get("content-type"),
    )

    # If there is a body but the client omitted Content-Type, default to JSON.
    if body and not any(k.lower() == "content-type" for k in headers.keys()):
        headers["Content-Type"] = "application/json"

    timeout_s = _get_timeout_seconds(s)
    client = get_async_httpx_client(timeout=timeout_s)

    effective_path = path_override or request.url.path
    if _is_sse_path(effective_path):
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
    """Forward the request to the same upstream path."""
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

    Supports two call styles:
      - New style (keyword-only):
          forward_openai_method_path(method=..., path=..., query=..., json_body=..., inbound_headers=...)
      - Legacy style (positional):
          forward_openai_method_path(<method>, <path>, <request>)
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
        api_key,
        content_type="application/json",
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


async def forward_responses_create(request: Request, body: Any) -> Response:
    """Convenience wrapper for POST /v1/responses using the proxy envelope body."""
    return await forward_openai_method_path(
        method="POST",
        path="/v1/responses",
        query=dict(request.query_params),
        json_body=body,
        inbound_headers=request.headers,
    )
