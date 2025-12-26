# app/api/forward_openai.py

from __future__ import annotations

import json
from typing import Any, Dict, Iterable, Mapping, Optional, Tuple, Union

import httpx
from fastapi import HTTPException, Request
from starlette.responses import Response, StreamingResponse

from app.core.settings import get_settings
from app.http_client import get_async_httpx_client
from app.utils.logger import relay_log as logger


def _openai_base_url(settings) -> str:
    base = (settings.OPENAI_BASE_URL or "https://api.openai.com").strip()
    return base.rstrip("/")


def _join_url(base: str, path: str) -> str:
    """
    Join base and path without double slashes.
    Keeps path absolute.
    """
    base = base.rstrip("/")
    if not path.startswith("/"):
        path = "/" + path
    return f"{base}{path}"


def build_upstream_url(
    request: Request,
    *,
    base_url: str,
    path_override: Optional[str] = None,
    query_override: Optional[str] = None,
) -> str:
    """
    Construct the upstream URL using either:
      - the inbound request path/query (default), or
      - explicit overrides (used by method_path helper)
    """
    upstream_path = path_override or request.url.path
    upstream_query = query_override if query_override is not None else request.url.query

    url = _join_url(base_url, upstream_path)
    if upstream_query:
        url = f"{url}?{upstream_query}"
    return url


def _filter_outbound_headers(inbound: Mapping[str, str]) -> Dict[str, str]:
    """
    Forward only safe headers upstream. Do not forward hop-by-hop headers.
    """
    drop = {
        "host",
        "content-length",
        "connection",
        "keep-alive",
        "proxy-authenticate",
        "proxy-authorization",
        "te",
        "trailers",
        "transfer-encoding",
        "upgrade",
    }

    out: Dict[str, str] = {}
    for k, v in inbound.items():
        lk = k.lower()
        if lk in drop:
            continue
        out[k] = v
    return out


def build_outbound_headers(
    request: Optional[Request],
    *,
    content_type: Optional[str] = None,
    extra_headers: Optional[Mapping[str, str]] = None,
    inbound_headers: Optional[Mapping[str, str]] = None,
) -> Dict[str, str]:
    """
    Build headers to send to upstream, including Authorization.
    `inbound_headers` is supported for call sites that don't have a full Request.
    """
    settings = get_settings()
    if not settings.OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY is not set")

    base_inbound: Mapping[str, str] = {}
    if request is not None:
        base_inbound = request.headers
    elif inbound_headers is not None:
        base_inbound = inbound_headers

    headers = _filter_outbound_headers(base_inbound)
    headers["Authorization"] = f"Bearer {settings.OPENAI_API_KEY}"

    if content_type:
        headers["Content-Type"] = content_type

    if extra_headers:
        for k, v in extra_headers.items():
            headers[k] = v

    return headers


def _filter_upstream_response_headers(upstream_headers: Mapping[str, str]) -> Dict[str, str]:
    """
    Filter hop-by-hop headers from upstream response before returning to client.
    """
    drop = {
        "content-encoding",
        "transfer-encoding",
        "connection",
        "keep-alive",
        "proxy-authenticate",
        "proxy-authorization",
        "te",
        "trailers",
        "upgrade",
    }
    out: Dict[str, str] = {}
    for k, v in upstream_headers.items():
        if k.lower() in drop:
            continue
        out[k] = v
    return out


async def forward_openai_request(request: Request) -> Response:
    """
    Generic passthrough:
      - forwards method, path, and querystring
      - forwards body (json/multipart/binary)
      - streams response if upstream is streaming
    """
    settings = get_settings()
    client = get_async_httpx_client()

    base = _openai_base_url(settings)
    url = build_upstream_url(request, base_url=base)

    content_type = request.headers.get("content-type")
    headers = build_outbound_headers(request, content_type=content_type)

    # Determine if this is likely streaming from the client side (Accept: text/event-stream)
    accept = (request.headers.get("accept") or "").lower()
    wants_stream = "text/event-stream" in accept

    try:
        body = await request.body()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read request body: {e}") from e

    logger.info("→ upstream %s %s", request.method, url)

    # If upstream is streaming SSE, we should stream back as well.
    # We do not attempt to parse SSE; we forward bytes.
    if wants_stream:
        try:
            upstream = await client.stream(
                request.method,
                url,
                headers=headers,
                content=body if body else None,
            )
        except Exception as e:
            raise HTTPException(status_code=424, detail={"detail": "Relay wiring error", "error": str(e)}) from e

        async def _aiter_bytes() -> Iterable[bytes]:
            async with upstream:
                async for chunk in upstream.aiter_bytes():
                    yield chunk

        resp_headers = _filter_upstream_response_headers(upstream.headers)
        media_type = upstream.headers.get("content-type")
        return StreamingResponse(
            _aiter_bytes(),
            status_code=upstream.status_code,
            headers=resp_headers,
            media_type=media_type,
        )

    # Non-streaming response
    try:
        r = await client.request(
            request.method,
            url,
            headers=headers,
            content=body if body else None,
        )
    except Exception as e:
        raise HTTPException(status_code=424, detail={"detail": "Relay wiring error", "error": str(e)}) from e

    resp_headers = _filter_upstream_response_headers(r.headers)
    media_type = r.headers.get("content-type")

    return Response(
        content=r.content,
        status_code=r.status_code,
        headers=resp_headers,
        media_type=media_type,
    )


async def forward_openai_method_path(
    *args: Any,
    **kwargs: Any,
) -> Union[Dict[str, Any], Any]:
    """
    Helper for routes that want to call an explicit upstream method/path with JSON.

    Supported call styles:

      forward_openai_method_path(method, path, request=request, json_body=..., extra_headers=...)
      forward_openai_method_path(method, path, inbound_headers=..., json_body=..., extra_headers=...)

    Returns parsed JSON (dict/list) or raises HTTPException.
    """
    if len(args) < 2:
        raise TypeError("forward_openai_method_path(method, path, ...) requires at least 2 positional args")

    method = str(args[0]).upper()
    upstream_path = str(args[1])

    request: Optional[Request] = kwargs.get("request")
    inbound_headers: Optional[Mapping[str, str]] = kwargs.get("inbound_headers")
    json_body: Optional[Any] = kwargs.get("json_body")
    query: Optional[Mapping[str, Any]] = kwargs.get("query")
    extra_headers: Optional[Mapping[str, str]] = kwargs.get("extra_headers")

    settings = get_settings()
    client = get_async_httpx_client()
    base = _openai_base_url(settings)

    query_str = ""
    if query:
        # stable query ordering not required for correctness here
        query_pairs = []
        for k, v in query.items():
            if v is None:
                continue
            query_pairs.append(f"{k}={v}")
        query_str = "&".join(query_pairs)

    url = _join_url(base, upstream_path)
    if query_str:
        url = f"{url}?{query_str}"

    headers = build_outbound_headers(
        request,
        content_type="application/json",
        extra_headers=extra_headers,
        inbound_headers=inbound_headers,
    )

    try:
        r = await client.request(
            method,
            url,
            headers=headers,
            content=json.dumps(json_body).encode("utf-8") if json_body is not None else None,
        )
    except Exception as e:
        raise HTTPException(status_code=424, detail={"detail": "Relay wiring error", "error": str(e)}) from e

    # Pass through upstream errors as-is (do not raise 5xx from relay)
    try:
        data = r.json()
    except Exception:
        # If upstream isn't JSON, return a structured error
        raise HTTPException(status_code=r.status_code, detail=r.text)

    if r.status_code >= 400:
        # Preserve upstream payload and status code
        raise HTTPException(status_code=r.status_code, detail=data)

    return data
