from __future__ import annotations

import json
from typing import Any, Dict, Mapping, Optional, Tuple, Union
from urllib.parse import urlencode

import httpx
from fastapi import Request
from fastapi.responses import Response, StreamingResponse

from app.core.config import get_settings
from app.core.http_client import get_async_httpx_client, get_async_openai_client
from app.utils.logger import relay_log

# Headers that should never be forwarded hop-by-hop (RFC 7230) or that break proxying.
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

# httpx may transparently decode content; avoid forwarding content-encoding in that case.
_STRIP_RESPONSE_HEADERS = set(_HOP_BY_HOP_HEADERS) | {"content-encoding"}


def _join_url(base: str, path: str) -> str:
    """
    Join base + path safely, avoiding accidental '/v1/v1' duplication.
    """
    base = (base or "").rstrip("/")
    path = (path or "").lstrip("/")

    if not base:
        base = "https://api.openai.com/v1"

    # If base already ends with /v1 and path begins with v1/..., avoid duplicating.
    if base.endswith("/v1") and (path == "v1" or path.startswith("v1/")):
        path = path[3:]  # strip leading "v1"
        path = path.lstrip("/")

    if path:
        return f"{base}/{path}"
    return base


def build_upstream_url(
    path: str,
    *,
    request: Optional[Request] = None,
    base_url: Optional[str] = None,
) -> str:
    """
    Build the full upstream URL for an OpenAI path.

    Supports:
      - build_upstream_url("/v1/responses")
      - build_upstream_url("/v1/containers/.../content", request=request, base_url=...)
    """
    s = get_settings()
    upstream_base = (base_url or getattr(s, "openai_base_url", None) or "https://api.openai.com/v1").rstrip("/")

    # Normalize path
    p = (path or "").strip()
    if not p.startswith("/"):
        p = "/" + p
    if not p.startswith("/v1"):
        p = "/v1" + p

    url = _join_url(upstream_base, p)

    # Append query from Request if provided
    if request is not None and getattr(request.url, "query", ""):
        url = f"{url}?{request.url.query}"

    return url


def _get_timeout_seconds(settings_obj: Optional[Any] = None) -> float:
    """
    Back-compat helper used by containers route.

    Reads timeout from the Settings object if possible; falls back safely.
    """
    s = settings_obj or get_settings()

    for attr in (
        "proxy_timeout_seconds",
        "PROXY_TIMEOUT_SECONDS",
        "proxy_timeout",
        "PROXY_TIMEOUT",
        "timeout_seconds",
        "TIMEOUT_SECONDS",
    ):
        if hasattr(s, attr):
            val = getattr(s, attr)
            if val is None:
                continue
            try:
                return float(val)
            except (TypeError, ValueError):
                continue

    # Match config default
    return 90.0


def build_outbound_headers(
    inbound_headers: Mapping[str, str],
    *,
    openai_api_key: Optional[str] = None,
    content_type: Optional[str] = "application/json",
    forward_accept: bool = True,
    accept: Optional[str] = None,
    path_hint: Optional[str] = None,
) -> Dict[str, str]:
    """
    Build outbound headers for upstream OpenAI.

    - Drops hop-by-hop headers
    - Replaces Authorization with server-side OPENAI_API_KEY
    - Optionally sets/overrides Content-Type and Accept
    """
    s = get_settings()
    api_key = openai_api_key or getattr(s, "openai_api_key", None)
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured (cannot forward to upstream).")

    outbound: Dict[str, str] = {}

    # Handle Accept explicitly so we can respect forward_accept + accept override.
    accept_value: Optional[str] = accept

    for k, v in inbound_headers.items():
        lk = k.lower()

        if lk in _HOP_BY_HOP_HEADERS:
            continue

        # Never forward client Authorization (relay auth); replace with upstream key.
        if lk == "authorization":
            continue

        # Content-Type: preserve multipart boundary if caller passes content_type=None
        if lk == "content-type":
            if content_type is None:
                outbound[k] = v
            # else: we override/set later
            continue

        if lk == "accept":
            if accept_value is None and forward_accept:
                accept_value = v
            # If forward_accept False, drop it.
            continue

        outbound[k] = v

    outbound["Authorization"] = f"Bearer {api_key}"

    # Optional OpenAI headers
    if getattr(s, "openai_organization", None):
        outbound["OpenAI-Organization"] = s.openai_organization
    if getattr(s, "openai_project", None):
        outbound["OpenAI-Project"] = s.openai_project
    if getattr(s, "openai_beta", None):
        outbound["OpenAI-Beta"] = s.openai_beta

    # Content-Type override
    if content_type is not None:
        outbound.setdefault("Content-Type", content_type)

    # Accept override / forward
    if accept_value is not None:
        outbound.setdefault("Accept", accept_value)

    if path_hint:
        # Safe, non-sensitive debug hint
        outbound.setdefault("X-Relay-Upstream-Path", path_hint)

    return outbound


def filter_upstream_headers(upstream_headers: Mapping[str, str]) -> Dict[str, str]:
    """
    Filter headers coming back from upstream OpenAI before returning to client.
    """
    filtered: Dict[str, str] = {}
    for k, v in upstream_headers.items():
        if k.lower() in _STRIP_RESPONSE_HEADERS:
            continue
        filtered[k] = v
    return filtered


# Back-compat alias (containers imports this exact name)
def filter_incoming_headers(upstream_headers: Mapping[str, str]) -> Dict[str, str]:
    return filter_upstream_headers(upstream_headers)


def _is_event_stream(content_type: Optional[str]) -> bool:
    return bool(content_type) and ("text/event-stream" in content_type.lower())


async def forward_openai_request(request: Request, upstream_path: Optional[str] = None) -> Response:
    """
    Forward an incoming FastAPI Request directly to OpenAI, preserving method + path + query.

    This is the default passthrough used by most route modules.
    """
    method = request.method.upper()
    path = upstream_path or request.url.path
    upstream_url = build_upstream_url(path, request=request)

    timeout_s = _get_timeout_seconds(get_settings())
    client = get_async_httpx_client(timeout=timeout_s)

    ct = request.headers.get("content-type") or ""
    is_multipart = ct.lower().startswith("multipart/form-data")

    headers = build_outbound_headers(
        inbound_headers=request.headers,
        content_type=None if is_multipart else (ct or None),
        forward_accept=True,
        accept=request.headers.get("accept"),
        path_hint=path,
    )

    # Build request body
    content: Optional[Union[bytes, Any]]
    if method in {"GET", "HEAD", "OPTIONS"}:
        content = None
    else:
        if is_multipart:
            # Stream multipart bodies to avoid buffering large uploads.
            content = request.stream()
        else:
            raw = await request.body()
            content = raw if raw else None

    upstream_req = client.build_request(method, upstream_url, headers=headers, content=content)

    try:
        upstream_resp = await client.send(upstream_req, stream=True, follow_redirects=True)
    except httpx.HTTPError as e:
        relay_log.exception("Upstream HTTP error: %s %s", method, upstream_url)
        return Response(
            content=json.dumps({"error": {"message": str(e), "type": "upstream_error"}}),
            status_code=502,
            media_type="application/json",
        )

    media_type = upstream_resp.headers.get("content-type")
    resp_headers = filter_upstream_headers(upstream_resp.headers)

    if _is_event_stream(media_type):
        async def event_bytes():
            try:
                async for chunk in upstream_resp.aiter_raw():
                    yield chunk
            finally:
                await upstream_resp.aclose()

        return StreamingResponse(
            event_bytes(),
            status_code=upstream_resp.status_code,
            headers=resp_headers,
            media_type=media_type,
        )

    body = await upstream_resp.aread()
    await upstream_resp.aclose()

    return Response(
        content=body,
        status_code=upstream_resp.status_code,
        headers=resp_headers,
        media_type=media_type,
    )


def _parse_forward_openai_method_path_args(
    args: Tuple[Any, ...],
    kwargs: Dict[str, Any],
) -> Tuple[str, str, Optional[Request], Optional[Mapping[str, Any]], Any, Mapping[str, str]]:
    """
    Support both call styles used in the repo:

    Legacy (videos):
      forward_openai_method_path("POST", "/v1/videos", request)

    Proxy (envelope):
      forward_openai_method_path(method=..., path=..., query=..., json_body=..., inbound_headers=...)
    """
    # Legacy positional: (method, path, request)
    if len(args) == 3 and isinstance(args[0], str) and isinstance(args[1], str):
        method = args[0]
        path = args[1]
        request = args[2]
        query = kwargs.get("query")
        body = kwargs.get("json_body", kwargs.get("body"))
        inbound_headers = getattr(request, "headers", {}) if request is not None else {}
        return method, path, request, query, body, inbound_headers

    # Keyword style
    request = kwargs.get("request")
    method = kwargs.get("method")
    path = kwargs.get("path")
    query = kwargs.get("query")
    body = kwargs.get("json_body", kwargs.get("body"))
    inbound_headers = kwargs.get("inbound_headers") or (request.headers if request is not None else {})

    if not method or not path:
        raise ValueError("forward_openai_method_path requires method and path.")

    return method, path, request, query, body, inbound_headers


async def forward_openai_method_path(*args: Any, **kwargs: Any) -> Response:
    """
    Forward an OpenAI request given an explicit method + path.

    Supports both the legacy positional call style (videos router) and the proxy keyword call style.
    """
    method, path, _request, query, body, inbound_headers = _parse_forward_openai_method_path_args(args, kwargs)

    timeout_s = _get_timeout_seconds(get_settings())
    client = get_async_httpx_client(timeout=timeout_s)

    upstream_url = build_upstream_url(path)

    if query:
        upstream_url = f"{upstream_url}?{urlencode(query, doseq=True)}"

    # Build JSON body for proxy-style calls
    content: Optional[bytes] = None
    m = method.upper()

    if m not in {"GET", "HEAD", "OPTIONS"}:
        if body is None:
            content = None
        elif isinstance(body, (bytes, bytearray)):
            content = bytes(body)
        else:
            content = json.dumps(body).encode("utf-8")

    headers = build_outbound_headers(
        inbound_headers=inbound_headers,
        content_type="application/json" if content is not None else None,
        forward_accept=True,
        accept=(inbound_headers.get("accept") if hasattr(inbound_headers, "get") else None),
        path_hint=path,
    )

    upstream_req = client.build_request(m, upstream_url, headers=headers, content=content)

    try:
        upstream_resp = await client.send(upstream_req, stream=True, follow_redirects=True)
    except httpx.HTTPError as e:
        relay_log.exception("Upstream HTTP error: %s %s", m, upstream_url)
        return Response(
            content=json.dumps({"error": {"message": str(e), "type": "upstream_error"}}),
            status_code=502,
            media_type="application/json",
        )

    media_type = upstream_resp.headers.get("content-type")
    resp_headers = filter_upstream_headers(upstream_resp.headers)

    if _is_event_stream(media_type):
        async def event_bytes():
            try:
                async for chunk in upstream_resp.aiter_raw():
                    yield chunk
            finally:
                await upstream_resp.aclose()

        return StreamingResponse(
            event_bytes(),
            status_code=upstream_resp.status_code,
            headers=resp_headers,
            media_type=media_type,
        )

    raw = await upstream_resp.aread()
    await upstream_resp.aclose()

    return Response(
        content=raw,
        status_code=upstream_resp.status_code,
        headers=resp_headers,
        media_type=media_type,
    )


def _maybe_model_dump(obj: Any) -> Any:
    """
    Convert OpenAI SDK Pydantic models to plain dicts when possible.
    """
    if hasattr(obj, "model_dump"):
        return obj.model_dump(exclude_none=True)
    if hasattr(obj, "dict"):
        return obj.dict(exclude_none=True)  # pragma: no cover
    return obj


async def forward_responses_create(payload: Dict[str, Any]) -> Any:
    """
    Typed forwarding for POST /v1/responses (non-stream).
    """
    client = get_async_openai_client()
    result = await client.responses.create(**payload)
    return _maybe_model_dump(result)


async def forward_embeddings_create(payload: Dict[str, Any]) -> Any:
    """
    Typed forwarding for POST /v1/embeddings.
    """
    client = get_async_openai_client()
    result = await client.embeddings.create(**payload)
    return _maybe_model_dump(result)
