from __future__ import annotations

import json
from typing import Any, AsyncIterator, Dict, Mapping, Optional, cast

import httpx
from fastapi import HTTPException, Request, Response
from fastapi.responses import StreamingResponse

try:
    # Project-provided settings + shared client (preferred)
    from app.core.config import get_settings  # type: ignore
except Exception:  # pragma: no cover
    get_settings = None  # type: ignore

try:
    from app.core.http_client import get_async_httpx_client  # type: ignore
except Exception:  # pragma: no cover

    async def get_async_httpx_client() -> httpx.AsyncClient:  # type: ignore
        # Fallback: per-call client. Prefer the project implementation for pooling.
        return httpx.AsyncClient()


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


def _get_openai_api_key() -> str:
    settings = get_settings() if callable(get_settings) else None
    key = getattr(settings, "openai_api_key", None) if settings is not None else None
    if not key:
        # Use a non-500 to signal relay wiring/config issues.
        raise HTTPException(
            status_code=424,
            detail="Relay wiring error: OPENAI_API_KEY is not configured on the relay server.",
        )
    return cast(str, key)


def _get_openai_base_url() -> str:
    settings = get_settings() if callable(get_settings) else None
    base = getattr(settings, "openai_base_url", None) if settings is not None else None
    return cast(str, base or "https://api.openai.com")


def _get_openai_org() -> Optional[str]:
    settings = get_settings() if callable(get_settings) else None
    return cast(Optional[str], getattr(settings, "openai_organization", None) if settings is not None else None)


def _get_openai_project() -> Optional[str]:
    settings = get_settings() if callable(get_settings) else None
    return cast(Optional[str], getattr(settings, "openai_project", None) if settings is not None else None)


def _get_timeout_seconds(settings: Any = None) -> float:
    """
    Return the upstream timeout (seconds).

    Backward compatible: some callers may pass a settings object.
    """
    settings_obj = settings or (get_settings() if callable(get_settings) else None)
    val = getattr(settings_obj, "relay_timeout_seconds", None) if settings_obj is not None else None
    try:
        return float(val) if val is not None else 60.0
    except Exception:
        return 60.0


def _join_url(base_url: str, path: str) -> str:
    base = base_url.rstrip("/")
    p = path if path.startswith("/") else f"/{path}"
    return f"{base}{p}"


def build_upstream_url(
    upstream_path: str,
    *,
    request: Optional[Request] = None,
    query: Optional[Mapping[str, str]] = None,
) -> str:
    """
    Build a full upstream OpenAI URL for the given path, merging query parameters.
    """
    url = httpx.URL(_join_url(_get_openai_base_url(), upstream_path))
    merged: Dict[str, str] = {}

    if request is not None:
        merged.update({k: str(v) for k, v in request.query_params.items()})

    if query is not None:
        merged.update({k: str(v) for k, v in query.items()})

    if merged:
        url = url.copy_merge_params(merged)

    return str(url)


def build_outbound_headers(inbound_headers: Mapping[str, str]) -> Dict[str, str]:
    """
    Build headers sent to upstream OpenAI.
    - Removes hop-by-hop / host / content-length
    - Replaces inbound Authorization (relay auth) with upstream OpenAI API key
    """
    out: Dict[str, str] = {}

    for k, v in inbound_headers.items():
        lk = k.lower()
        if lk in _HOP_BY_HOP_HEADERS:
            continue
        if lk in {"host", "content-length"}:
            continue
        if lk == "authorization":
            # Do NOT forward relay auth.
            continue
        out[k] = v

    out["Authorization"] = f"Bearer {_get_openai_api_key()}"

    org = _get_openai_org()
    if org:
        out["OpenAI-Organization"] = org

    proj = _get_openai_project()
    if proj:
        out["OpenAI-Project"] = proj

    return out


def filter_upstream_headers(upstream_headers: httpx.Headers) -> Dict[str, str]:
    """
    Filter upstream headers for downstream clients.
    """
    out: Dict[str, str] = {}
    for k, v in upstream_headers.items():
        lk = k.lower()
        if lk in _HOP_BY_HOP_HEADERS:
            continue
        if lk in {"content-length", "content-encoding"}:
            # Avoid mismatches with StreamingResponse and downstream decoding.
            continue
        out[k] = v
    return out


def _is_event_stream_content_type(content_type: Optional[str]) -> bool:
    return bool(content_type and "text/event-stream" in content_type.lower())


def _detect_wants_stream(
    *,
    accept_header: str,
    path: str,
    content_type: Optional[str],
    body_bytes: bytes,
) -> bool:
    if "text/event-stream" in (accept_header or "").lower():
        return True
    if path.endswith(":stream"):
        return True
    if content_type and "application/json" in content_type.lower() and body_bytes:
        try:
            payload = json.loads(body_bytes.decode("utf-8"))
            return bool(isinstance(payload, dict) and payload.get("stream") is True)
        except Exception:
            return False
    return False


async def _stream_bytes(resp: httpx.Response, *, aexit) -> AsyncIterator[bytes]:
    try:
        async for chunk in resp.aiter_raw():
            if chunk:
                yield chunk
    finally:
        await aexit(None, None, None)


async def _forward_streaming_response(
    *,
    client: httpx.AsyncClient,
    method: str,
    url: str,
    headers: Dict[str, str],
    content: Optional[bytes],
    json_body: Any = None,
    timeout: float,
) -> Response:
    cm = client.stream(
        method,
        url,
        headers=headers,
        content=content,
        json=json_body,
        timeout=timeout,
        follow_redirects=False,
    )
    resp = await cm.__aenter__()

    # If upstream isn't SSE, buffer and return a normal Response.
    if not _is_event_stream_content_type(resp.headers.get("content-type")):
        body = await resp.aread()
        await cm.__aexit__(None, None, None)
        return Response(
            content=body,
            status_code=resp.status_code,
            headers=filter_upstream_headers(resp.headers),
            media_type=resp.headers.get("content-type"),
        )

    return StreamingResponse(
        _stream_bytes(resp, aexit=cm.__aexit__),
        status_code=resp.status_code,
        headers=filter_upstream_headers(resp.headers),
        media_type=resp.headers.get("content-type"),
    )


async def forward_openai_request(
    request: Request,
    *,
    upstream_path: Optional[str] = None,
    method: Optional[str] = None,
    query: Optional[Mapping[str, str]] = None,
) -> Response:
    """
    Forward an incoming FastAPI Request to upstream OpenAI.
    """
    upstream_path_final = upstream_path or request.url.path
    method_final = (method or request.method).upper()

    url = build_upstream_url(upstream_path_final, request=request, query=query)
    headers = build_outbound_headers(request.headers)

    body = await request.body()
    accept = request.headers.get("accept", "")
    content_type = request.headers.get("content-type")

    wants_stream = _detect_wants_stream(
        accept_header=accept,
        path=upstream_path_final,
        content_type=content_type,
        body_bytes=body,
    )

    client = await get_async_httpx_client()
    timeout = _get_timeout_seconds()

    if wants_stream:
        return await _forward_streaming_response(
            client=client,
            method=method_final,
            url=url,
            headers=headers,
            content=body if body else None,
            timeout=timeout,
        )

    resp = await client.request(
        method_final,
        url,
        headers=headers,
        content=body if body else None,
        timeout=timeout,
        follow_redirects=False,
    )
    return Response(
        content=resp.content,
        status_code=resp.status_code,
        headers=filter_upstream_headers(resp.headers),
        media_type=resp.headers.get("content-type"),
    )


async def forward_openai_method_path(
    *,
    method: str,
    path: str,
    request: Optional[Request] = None,
    inbound_headers: Optional[Mapping[str, str]] = None,
    query: Optional[Mapping[str, str]] = None,
    json_body: Any = None,
    content: Optional[bytes] = None,
) -> Response:
    """
    Forward an arbitrary method/path to upstream OpenAI.
    """
    url = build_upstream_url(path, request=request, query=query)
    hdrs = inbound_headers or (request.headers if request is not None else {})
    headers = build_outbound_headers(hdrs)

    accept = cast(str, hdrs.get("accept", ""))
    wants_stream = bool(
        ("text/event-stream" in (accept or "").lower())
        or path.endswith(":stream")
        or (isinstance(json_body, dict) and json_body.get("stream") is True)
    )

    client = await get_async_httpx_client()
    timeout = _get_timeout_seconds()

    if wants_stream:
        return await _forward_streaming_response(
            client=client,
            method=method.upper(),
            url=url,
            headers=headers,
            content=content,
            json_body=json_body,
            timeout=timeout,
        )

    resp = await client.request(
        method.upper(),
        url,
        headers=headers,
        json=json_body if json_body is not None else None,
        content=content,
        timeout=timeout,
        follow_redirects=False,
    )
    return Response(
        content=resp.content,
        status_code=resp.status_code,
        headers=filter_upstream_headers(resp.headers),
        media_type=resp.headers.get("content-type"),
    )


async def forward_embeddings_create(
    body: Dict[str, Any],
    *,
    inbound_headers: Optional[Mapping[str, str]] = None,
) -> Dict[str, Any]:
    """
    Convenience helper used by /v1/embeddings route.
    """
    url = build_upstream_url("/v1/embeddings")
    headers = build_outbound_headers(inbound_headers or {})
    client = await get_async_httpx_client()
    timeout = _get_timeout_seconds()

    resp = await client.post(url, headers=headers, json=body, timeout=timeout, follow_redirects=False)
    try:
        payload = resp.json()
    except Exception:
        payload = {"error": {"message": resp.text}}

    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail=payload)

    return cast(Dict[str, Any], payload)


# ---------------------------------------------------------------------------
# Compatibility aliases (older modules imported underscored helpers)
# ---------------------------------------------------------------------------

_build_outbound_headers = build_outbound_headers
_filter_response_headers = filter_upstream_headers


def _join_upstream_url(base_url: str, upstream_path: str, query: Optional[Mapping[str, str]] = None) -> str:
    url = httpx.URL(_join_url(base_url, upstream_path))
    if query:
        url = url.copy_merge_params({k: str(v) for k, v in query.items()})
    return str(url)
