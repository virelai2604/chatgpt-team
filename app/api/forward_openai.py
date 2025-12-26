from __future__ import annotations

from typing import Any, AsyncIterator, Dict, Iterable, Mapping, Optional, Tuple

import httpx
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse, Response, StreamingResponse

from app.core.settings import get_settings
from app.http_client import get_async_httpx_client

# ----------------------------
# Header handling
# ----------------------------

_HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
}

_STRIP_REQUEST_HEADERS = {
    "host",
    "content-length",
    "accept-encoding",  # let httpx manage
    *(_HOP_BY_HOP_HEADERS),
}


def _iter_header_items(headers: Any) -> Iterable[Tuple[str, str]]:
    """
    Accepts:
      - Starlette/FastAPI Headers
      - dict-like
      - iterable of (k, v)
    """
    if headers is None:
        return []
    if hasattr(headers, "items"):
        return list(headers.items())
    return list(headers)


def build_outbound_headers(
    inbound_headers: Any,
    *,
    extra_headers: Optional[Mapping[str, str]] = None,
) -> Dict[str, str]:
    """
    Build safe upstream headers.

    Notes:
      - We intentionally do NOT forward the inbound Authorization header.
      - Upstream auth is injected from server-side settings.
    """
    settings = get_settings()

    out: Dict[str, str] = {}
    for k, v in _iter_header_items(inbound_headers):
        lk = str(k).lower()
        if lk in _STRIP_REQUEST_HEADERS:
            continue
        if lk == "authorization":
            continue
        out[str(k)] = str(v)

    # Inject upstream auth
    api_key = getattr(settings, "OPENAI_API_KEY", None)
    if api_key:
        out["Authorization"] = f"Bearer {api_key}"

    # Optional org/project
    org = getattr(settings, "OPENAI_ORG_ID", None)
    if org:
        out["OpenAI-Organization"] = str(org)
    proj = getattr(settings, "OPENAI_PROJECT_ID", None)
    if proj:
        out["OpenAI-Project"] = str(proj)

    if extra_headers:
        for k, v in extra_headers.items():
            out[str(k)] = str(v)

    return out


def filter_upstream_headers(upstream_headers: Mapping[str, str]) -> Dict[str, str]:
    """
    Remove hop-by-hop headers and any headers that are unsafe to forward verbatim.
    """
    out: Dict[str, str] = {}
    for k, v in upstream_headers.items():
        lk = k.lower()
        if lk in _HOP_BY_HOP_HEADERS or lk == "content-encoding":
            continue
        # content-length will be set by Starlette for non-streaming responses
        if lk == "content-length":
            continue
        out[k] = v
    return out


# Backwards-compatible names used by app.api.sse (and potentially older modules)
_build_outbound_headers = build_outbound_headers
_filter_response_headers = filter_upstream_headers


# ----------------------------
# URL helpers
# ----------------------------

def _openai_base_url() -> str:
    settings = get_settings()
    base = getattr(settings, "OPENAI_API_BASE", None) or "https://api.openai.com/v1"
    return str(base).rstrip("/")


def _join_upstream_url(base: str, path: str, query: str = "") -> str:
    """
    Join base + path with correct /v1 de-duplication.

    Supports an optional third argument (query) because older code called it as:
      _join_upstream_url(base, path, request.url.query)
    """
    base_s = str(base).rstrip("/")
    path_s = str(path).strip()

    q = str(query).strip()
    if q and not q.startswith("?"):
        q = "?" + q.lstrip("?")

    if not path_s.startswith("/"):
        path_s = "/" + path_s

    # Avoid "/v1/v1" when base already ends with "/v1"
    if base_s.endswith("/v1") and path_s.startswith("/v1/"):
        path_s = path_s[3:]  # drop leading "/v1"

    return f"{base_s}{path_s}{q}"


def build_upstream_url(
    upstream_path: str,
    *,
    query: Optional[Mapping[str, Any]] = None,
    raw_query: str = "",
) -> str:
    if query and raw_query:
        raise ValueError("Provide either query= or raw_query=, not both.")

    if query:
        qp = httpx.QueryParams({k: v for k, v in query.items() if v is not None})
        raw_query = str(qp)

    return _join_upstream_url(_openai_base_url(), upstream_path, raw_query)


# ----------------------------
# Forwarders
# ----------------------------

async def _streaming_iterator(resp: httpx.Response) -> AsyncIterator[bytes]:
    try:
        async for chunk in resp.aiter_raw():
            if chunk:
                yield chunk
    finally:
        await resp.aclose()


async def _get_client() -> httpx.AsyncClient:
    """
    get_async_httpx_client() is expected to return an httpx.AsyncClient, but we
    also tolerate it being an async factory (awaitable) to avoid subtle import/version drift.
    """
    client = get_async_httpx_client()
    if hasattr(client, "__await__"):
        client = await client  # type: ignore[assignment]
    return client  # type: ignore[return-value]


async def forward_openai_request(
    request: Request,
    *,
    upstream_path: Optional[str] = None,
    method: Optional[str] = None,
    json_body: Any = None,
    extra_headers: Optional[Mapping[str, str]] = None,
    stream: bool = False,
) -> Response:
    """
    Forward an incoming FastAPI Request to the OpenAI upstream.

    - If json_body is provided, it overrides the inbound body and is sent as JSON.
    - If stream=True, returns a StreamingResponse that proxies upstream bytes.
    """
    try:
        upstream_method = (method or request.method).upper()
        upstream_path = upstream_path or request.url.path
        upstream_url = build_upstream_url(upstream_path, raw_query=request.url.query)

        headers = build_outbound_headers(request.headers, extra_headers=extra_headers)
        client = await _get_client()

        req_kwargs: Dict[str, Any] = {}
        if json_body is not None:
            req_kwargs["json"] = json_body
            if "content-type" not in {k.lower() for k in headers}:
                headers["Content-Type"] = "application/json"
        else:
            # stream request body to avoid buffering large uploads
            req_kwargs["content"] = request.stream()

        if stream:
            req = client.build_request(upstream_method, upstream_url, headers=headers, **req_kwargs)
            upstream_resp = await client.send(req, stream=True)
            return StreamingResponse(
                _streaming_iterator(upstream_resp),
                status_code=upstream_resp.status_code,
                headers=filter_upstream_headers(upstream_resp.headers),
                media_type=upstream_resp.headers.get("content-type"),
            )

        resp = await client.request(upstream_method, upstream_url, headers=headers, **req_kwargs)
        return Response(
            content=resp.content,
            status_code=resp.status_code,
            headers=filter_upstream_headers(resp.headers),
            media_type=resp.headers.get("content-type"),
        )

    except httpx.HTTPError as e:
        return JSONResponse(
            status_code=502,
            content={"error": {"message": f"Upstream HTTP error: {str(e)}", "type": "relay_upstream_error"}},
        )
    except Exception as e:
        return JSONResponse(
            status_code=424,
            content={"error": {"message": f"Relay wiring error: {str(e)}", "type": "relay_wiring_error"}},
        )


async def forward_openai_method_path(
    method: str,
    path: Optional[str] = None,
    request: Optional[Request] = None,
    *,
    upstream_path: Optional[str] = None,
    query: Optional[Mapping[str, Any]] = None,
    inbound_headers: Any = None,
    json_body: Any = None,
    content: Optional[bytes] = None,
    extra_headers: Optional[Mapping[str, str]] = None,
    stream: bool = False,
) -> Response:
    """
    Forward a request when you have method/path and optionally:
      - request (for querystring + headers)
      - inbound_headers (if you don't have a Request object)
      - query (dict query params)
      - json_body or raw content

    Compatibility:
      - `path` is treated as the upstream path (alias of upstream_path).
      - Callers may pass method=..., path=... as keyword args.
    """
    upstream_path = upstream_path or path
    if not upstream_path:
        raise HTTPException(status_code=500, detail="forward_openai_method_path missing upstream path")

    if request is not None and inbound_headers is None:
        inbound_headers = request.headers
    if inbound_headers is None:
        inbound_headers = {}

    raw_query = request.url.query if request is not None else ""
    if query and raw_query:
        merged = dict(httpx.QueryParams(raw_query))
        merged.update({k: v for k, v in query.items() if v is not None})
        upstream_url = build_upstream_url(upstream_path, query=merged, raw_query="")
    else:
        upstream_url = build_upstream_url(upstream_path, query=query, raw_query=raw_query)

    headers = build_outbound_headers(inbound_headers, extra_headers=extra_headers)
    client = await _get_client()

    req_kwargs: Dict[str, Any] = {}
    if json_body is not None:
        req_kwargs["json"] = json_body
        if "content-type" not in {k.lower() for k in headers}:
            headers["Content-Type"] = "application/json"
    elif content is not None:
        req_kwargs["content"] = content

    m = method.upper()

    if stream:
        req = client.build_request(m, upstream_url, headers=headers, **req_kwargs)
        upstream_resp = await client.send(req, stream=True)
        return StreamingResponse(
            _streaming_iterator(upstream_resp),
            status_code=upstream_resp.status_code,
            headers=filter_upstream_headers(upstream_resp.headers),
            media_type=upstream_resp.headers.get("content-type"),
        )

    resp = await client.request(m, upstream_url, headers=headers, **req_kwargs)
    return Response(
        content=resp.content,
        status_code=resp.status_code,
        headers=filter_upstream_headers(resp.headers),
        media_type=resp.headers.get("content-type"),
    )
