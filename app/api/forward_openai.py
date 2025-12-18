from __future__ import annotations

import json
from typing import Any, Mapping, Optional
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import httpx
from fastapi import HTTPException, Request
from fastapi.responses import Response, StreamingResponse

from app.core.http_client import get_async_httpx_client, get_async_openai_client
from app.utils.logger import relay_log

# Settings access (supports either get_settings() or a module-level settings object).
try:
    from app.core.config import get_settings  # type: ignore
except ImportError:  # pragma: no cover
    from app.core.config import settings as _settings  # type: ignore

    def get_settings():
        return _settings


# -------------------------
# URL + header normalization
# -------------------------

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


def normalize_base_url(base_url: str) -> str:
    """Normalize base to scheme://host[:port] (no trailing /, no /v1)."""
    base = (base_url or "").strip()
    if not base:
        return "https://api.openai.com"
    base = base.rstrip("/")
    if base.endswith("/v1"):
        base = base[: -len("/v1")]
    return base.rstrip("/")


def normalize_upstream_path(path: str) -> str:
    """Ensure path starts with /v1."""
    p = (path or "").strip()
    if not p.startswith("/"):
        p = "/" + p
    if not p.startswith("/v1/") and p != "/v1":
        # allow callers to pass "/responses" or "/v1/responses"
        if p.startswith("/"):
            p = "/v1" + p
        else:
            p = "/v1/" + p
    return p


def build_upstream_url(path: str) -> str:
    settings = get_settings()
    base = normalize_base_url(getattr(settings, "openai_base_url", "https://api.openai.com"))
    p = normalize_upstream_path(path)
    return f"{base}{p}"


def filter_upstream_headers(headers: Mapping[str, str]) -> dict[str, str]:
    """Strip hop-by-hop headers and anything that shouldn't be forwarded back to the client."""
    out: dict[str, str] = {}
    for k, v in headers.items():
        lk = k.lower()
        if lk in _HOP_BY_HOP_HEADERS:
            continue
        # Let FastAPI/Uvicorn manage content-length/transfer-encoding.
        if lk in {"content-length", "transfer-encoding"}:
            continue
        out[k] = v
    return out


def build_outbound_headers(
    inbound_headers: Optional[Mapping[str, str]] = None,
    *,
    content_type: Optional[str] = None,
    accept: Optional[str] = None,
) -> dict[str, str]:
    """Build headers for upstream OpenAI call.

    - Uses server-side OpenAI API key
    - Does NOT forward inbound Authorization
    - Forwards safe headers (User-Agent, OpenAI-Organization/Project, etc.)
    """
    settings = get_settings()
    api_key = getattr(settings, "openai_api_key", None)
    if not api_key:
        raise HTTPException(status_code=500, detail="Server is missing OPENAI_API_KEY")

    outbound: dict[str, str] = {
        "Authorization": f"Bearer {api_key}",
    }

    if inbound_headers:
        passthrough_allow = {
            "user-agent",
            "openai-organization",
            "openai-project",
            "openai-beta",
        }
        for k, v in inbound_headers.items():
            lk = k.lower()
            if lk in passthrough_allow:
                outbound[k] = v

    if content_type:
        outbound["Content-Type"] = content_type
    if accept:
        outbound["Accept"] = accept

    return outbound


def _normalize_query_params(query: Optional[Mapping[str, Any]]) -> list[tuple[str, str]]:
    if not query:
        return []
    items: list[tuple[str, str]] = []
    for k, v in query.items():
        if v is None:
            continue
        if isinstance(v, (list, tuple)):
            for vv in v:
                if vv is None:
                    continue
                items.append((str(k), str(vv)))
        else:
            items.append((str(k), str(v)))
    return items


def _get_timeout_seconds(request: Optional[Request] = None) -> float:
    """Centralized request timeout selection."""
    settings = get_settings()
    timeout = getattr(settings, "proxy_timeout_seconds", None)
    if timeout is None:
        timeout = getattr(settings, "relay_timeout_seconds", 120)
    try:
        return float(timeout)
    except Exception:
        return 120.0


def _maybe_model_dump(obj: Any) -> Any:
    """Convert OpenAI SDK objects to plain JSON-serializable dicts when possible."""
    if obj is None:
        return None
    if hasattr(obj, "model_dump"):
        try:
            return obj.model_dump()
        except Exception:
            pass
    if hasattr(obj, "dict"):
        try:
            return obj.dict()
        except Exception:
            pass
    return obj


# -------------------------
# Generic passthrough forwarder
# -------------------------

async def forward_openai_request(request: Request, upstream_path: str) -> Response:
    """Forward an inbound FastAPI request to OpenAI upstream.

    Supports:
    - JSON requests
    - multipart/form-data uploads (streamed)
    - SSE streaming responses (if upstream returns text/event-stream)
    - binary responses
    """
    upstream_url = build_upstream_url(upstream_path)
    timeout = _get_timeout_seconds(request)

    # Decide whether to stream request body
    content_type = request.headers.get("content-type", "")
    is_multipart = content_type.startswith("multipart/form-data")

    outbound_headers = build_outbound_headers(
        request.headers,
        content_type=None if is_multipart else content_type or None,
        accept=request.headers.get("accept"),
    )

    client = get_async_httpx_client()

    relay_log.info("Forwarding %s %s", request.method, upstream_path)

    if is_multipart:
        # Stream body directly to upstream (avoid buffering large uploads)
        async def body_iter():
            async for chunk in request.stream():
                yield chunk

        upstream_resp = await client.request(
            method=request.method,
            url=upstream_url,
            headers=outbound_headers,
            params=request.query_params,
            content=body_iter(),
            timeout=timeout,
        )
    else:
        raw = await request.body()
        upstream_resp = await client.request(
            method=request.method,
            url=upstream_url,
            headers=outbound_headers,
            params=request.query_params,
            content=raw if raw else None,
            timeout=timeout,
        )

    media_type = upstream_resp.headers.get("content-type")

    # If SSE, stream it through
    if media_type and media_type.startswith("text/event-stream"):
        async def sse_stream():
            async for line in upstream_resp.aiter_lines():
                yield (line + "\n").encode("utf-8")

        return StreamingResponse(
            sse_stream(),
            status_code=upstream_resp.status_code,
            headers=filter_upstream_headers(upstream_resp.headers),
            media_type=media_type,
        )

    # Otherwise, return buffered content
    content = await upstream_resp.aread()
    return Response(
        content=content,
        status_code=upstream_resp.status_code,
        headers=filter_upstream_headers(upstream_resp.headers),
        media_type=media_type,
    )


# -------------------------
# JSON-envelope proxy helper
# -------------------------

async def forward_openai_method_path(
    *,
    method: str,
    path: str,
    request: Optional[Request] = None,
    query: Optional[Mapping[str, Any]] = None,
    json_body: Optional[Any] = None,
    body: Optional[Any] = None,
    inbound_headers: Optional[Mapping[str, str]] = None,
    headers: Optional[Mapping[str, str]] = None,
) -> Response:
    """Forward an OpenAI API call expressed as method + path (+ optional JSON + query).

    This is used by the /v1/proxy route (JSON envelope).
    """

    # Backward-compatible aliases:
    # - some callers pass `headers=` instead of `inbound_headers=`
    # - some callers pass `body=` instead of `json_body=`
    if inbound_headers is None and headers is not None:
        inbound_headers = headers
    if inbound_headers is None and request is not None:
        inbound_headers = request.headers
    if json_body is None and body is not None:
        json_body = body

    upstream_url = build_upstream_url(path)
    timeout = _get_timeout_seconds(request)

    params = _normalize_query_params(query)
    content_type = "application/json" if json_body is not None else None
    outbound_headers = build_outbound_headers(inbound_headers, content_type=content_type)

    client = get_async_httpx_client()

    payload_bytes: Optional[bytes] = None
    if json_body is not None:
        payload_bytes = json.dumps(json_body).encode("utf-8")

    relay_log.info("Proxy-forward %s %s", method.upper(), path)

    upstream_resp = await client.request(
        method=method.upper(),
        url=upstream_url,
        headers=outbound_headers,
        params=params,
        content=payload_bytes,
        timeout=timeout,
    )

    media_type = upstream_resp.headers.get("content-type")
    content = await upstream_resp.aread()

    return Response(
        content=content,
        status_code=upstream_resp.status_code,
        headers=filter_upstream_headers(upstream_resp.headers),
        media_type=media_type,
    )


# -------------------------
# Higher-level helpers used by routes
# -------------------------

async def forward_responses_create(*, request: Request) -> dict[str, Any]:
    client = get_async_openai_client()
    payload = await request.json()
    relay_log.info("Forward /v1/responses via SDK")
    result = await client.responses.create(**payload)
    return _maybe_model_dump(result)


async def forward_embeddings_create(*, request: Request) -> dict[str, Any]:
    client = get_async_openai_client()
    payload = await request.json()
    relay_log.info("Forward /v1/embeddings via SDK")
    result = await client.embeddings.create(**payload)
    return _maybe_model_dump(result)


async def forward_files_list(*, request: Request) -> dict[str, Any]:
    client = get_async_openai_client()
    params = dict(request.query_params)
    result = await client.files.list(**params)
    return _maybe_model_dump(result)


async def forward_files_create(*, request: Request) -> dict[str, Any]:
    # Files create is multipart; use generic forwarder path in route (preferred).
    # This helper exists for compatibility with some route variants.
    raise HTTPException(status_code=400, detail="Use multipart passthrough for file uploads")


async def forward_files_retrieve(*, file_id: str) -> dict[str, Any]:
    client = get_async_openai_client()
    result = await client.files.retrieve(file_id)
    return _maybe_model_dump(result)


async def forward_files_delete(*, file_id: str) -> dict[str, Any]:
    client = get_async_openai_client()
    result = await client.files.delete(file_id)
    return _maybe_model_dump(result)
