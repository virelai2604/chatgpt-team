from __future__ import annotations

import json
from typing import Any, Dict, Mapping, Optional
from urllib.parse import urlencode

import httpx
from fastapi import HTTPException, Request, Response
from starlette.responses import StreamingResponse

from app.core.http_client import get_async_httpx_client
from app.core.settings import get_settings

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

# Some upstream responses include these and Starlette will handle encoding itself.
_STRIP_RESPONSE_HEADERS = _HOP_BY_HOP_HEADERS | {
    "content-length",
    "content-encoding",
}


def _get_timeout_seconds(settings: Any) -> float:
    # Settings uses timeout_seconds in your project; keep a defensive fallback.
    v = getattr(settings, "timeout_seconds", None)
    try:
        return float(v) if v is not None else 60.0
    except Exception:
        return 60.0


def _join_upstream_url(base: str, path: str) -> str:
    base = base.rstrip("/")
    if not path.startswith("/"):
        path = "/" + path
    return f"{base}{path}"


def _normalize_upstream_base(base: str, path: str) -> str:
    normalized = base.rstrip("/")
    if path.startswith("/v1") and normalized.endswith("/v1"):
        normalized = normalized[: -len("/v1")]
    return normalized
    

def _join_upstream_url_compat(*args: Any, **kwargs: Any) -> str:
    """
    Back-compat shim.

    Your SSE wiring previously called _join_upstream_url_compat() with 3 positional args,
    which must not crash the relay. We accept extra args and ignore them.
    """
    if len(args) >= 2:
        return _join_upstream_url(str(args[0]), str(args[1]))
    base = str(kwargs.get("base", "")).rstrip("/")
    path = str(kwargs.get("path", ""))
    return _join_upstream_url(base, path)


def build_upstream_url(
    path: str,
    *,
    request: Optional[Request] = None,
    query: Optional[Mapping[str, str]] = None,
    base_url: Optional[str] = None,
) -> str:
    """
    Build the upstream URL (api.openai.com or configured base) + path + querystring.
    """
    settings = get_settings()
    base = (
        base_url
        or getattr(settings, "UPSTREAM_BASE_URL", None)
        or getattr(settings, "OPENAI_API_BASE", None)
        or "https://api.openai.com"
    )
    
    normalized_base = _normalize_upstream_base(str(base), path)
    url = _join_upstream_url(normalized_base, path)


    # Use explicit query override if provided; else forward inbound query params.
    q: Dict[str, str] = {}
    if query:
        q.update({str(k): str(v) for k, v in query.items()})
    elif request is not None:
        # request.query_params is MultiDict; best-effort collapse (tests only need wiring).
        for k, v in request.query_params.items():
            q[str(k)] = str(v)

    if q:
        url = f"{url}?{urlencode(q, doseq=True)}"

    return url


def build_outbound_headers(
    inbound_headers: Mapping[str, str],
    *,
    content_type: Optional[str] = None,
    forward_accept: bool = False,
    path_hint: Optional[str] = None,
) -> Dict[str, str]:
    """
    Copy inbound headers, strip hop-by-hop, and set upstream Authorization.
    """
    settings = get_settings()
    upstream_key = getattr(settings, "OPENAI_API_KEY", None)
    if not upstream_key:
        # If you hit this, your env is wrong; tests usually skip without a real key.
        raise HTTPException(status_code=424, detail="Missing OPENAI_API_KEY")

    out: Dict[str, str] = {}

    for k, v in inbound_headers.items():
        lk = k.lower()
        if lk in _HOP_BY_HOP_HEADERS:
            continue
        if lk in {"host", "content-length"}:
            continue
        if lk == "authorization":
            continue
        if lk == "accept-encoding":
            continue
        out[k] = v
        
    out["Authorization"] = f"Bearer {upstream_key}"

    if content_type:
        out["Content-Type"] = str(content_type)

    if forward_accept and "Accept" not in out and "accept" not in out:
        accept_header = inbound_headers.get("accept") or inbound_headers.get("Accept")
        if accept_header:
            out["Accept"] = accept_header

    out["Accept-Encoding"] = "identity"

    # Optional: forward OpenAI project/org headers if present in Settings (do not invent).
    org = getattr(settings, "OPENAI_ORG_ID", None) or getattr(settings, "OPENAI_ORGANIZATION", None)
    if org and "OpenAI-Organization" not in out:
        out["OpenAI-Organization"] = str(org)

    project = getattr(settings, "OPENAI_PROJECT", None)
    if project and "OpenAI-Project" not in out:
        out["OpenAI-Project"] = str(project)

    beta = getattr(settings, "OPENAI_ASSISTANTS_BETA", None)
    if beta and path_hint and path_hint.startswith("/v1/uploads"):
        out.setdefault("OpenAI-Beta", str(beta))
        
    return out


def filter_upstream_headers(inbound_headers: Mapping[str, str]) -> Dict[str, str]:
    # Backwards-compatible name used by containers.py
    return build_outbound_headers(inbound_headers)


def _filter_response_headers(headers: Mapping[str, str]) -> Dict[str, str]:
    """
    Strip hop-by-hop and Starlette-conflicting headers.
    """
    out: Dict[str, str] = {}
    for k, v in headers.items():
        lk = k.lower()
        if lk in _STRIP_RESPONSE_HEADERS:
            continue
        out[k] = v
    return out


def _detect_wants_stream(*, accept_header: str, content_type: Optional[str], body_bytes: bytes) -> bool:
    if "text/event-stream" in (accept_header or "").lower():
        return True

    if content_type and "application/json" in content_type.lower():
        # Best-effort JSON parse to detect {"stream": true}
        try:
            obj = json.loads(body_bytes.decode("utf-8"))
            if isinstance(obj, dict) and obj.get("stream") is True:
                return True
        except Exception:
            pass

    return False


async def forward_openai_request(
    request: Request,
    *,
    upstream_path: Optional[str] = None,
    method: Optional[str] = None,
    query: Optional[Mapping[str, str]] = None,
) -> Response:
    """
    Forward an incoming FastAPI Request to upstream OpenAI.

    Critical: get_async_httpx_client() returns an AsyncClient and must NOT be awaited.
    """
    settings = get_settings()
    upstream_path_final = upstream_path or request.url.path
    method_final = (method or request.method).upper()

    url = build_upstream_url(upstream_path_final, request=request, query=query)
    headers = build_outbound_headers(request.headers, path_hint=upstream_path_final)    headers = build_outbound_headers(request.headers)

    body = await request.body()
    accept = request.headers.get("accept", "")
    content_type = request.headers.get("content-type")

    wants_stream = _detect_wants_stream(
        accept_header=accept,
        content_type=content_type,
        body_bytes=body,
    )

    client = get_async_httpx_client()
    timeout_s = _get_timeout_seconds(settings)

    if wants_stream:
        upstream_cm = client.stream(method_final, url, headers=headers, content=body, timeout=timeout_s)
        upstream_resp = await upstream_cm.__aenter__()

        async def _iter() -> Any:
            try:
                async for chunk in upstream_resp.aiter_bytes():
                    yield chunk
            finally:
                await upstream_cm.__aexit__(None, None, None)

        media_type = upstream_resp.headers.get("content-type") or "text/event-stream"
        return StreamingResponse(
            _iter(),
            status_code=upstream_resp.status_code,
            headers=_filter_response_headers(upstream_resp.headers),
            media_type=media_type,
        )

    try:
        upstream_resp = await client.request(
            method_final,
            url,
            headers=headers,
            content=body,
            timeout=timeout_s,
        )
    except httpx.HTTPError as e:
        raise HTTPException(status_code=424, detail=f"Upstream request failed: {type(e).__name__}: {e}") from e

    return Response(
        content=upstream_resp.content,
        status_code=upstream_resp.status_code,
        headers=_filter_response_headers(upstream_resp.headers),
        media_type=upstream_resp.headers.get("content-type"),
    )


async def forward_openai_method_path(
    method: str,
    path: str,
    *,
    json_body: Optional[Any] = None,
    inbound_headers: Optional[Mapping[str, str]] = None,
    request: Optional[Request] = None,
    query: Optional[Mapping[str, str]] = None,
) -> Response:
    """
    Forward a synthetic request (method + path) to upstream OpenAI.

    Must accept positional (method, path) because routes call:
      forward_openai_method_path("POST", "/v1/responses", ...)

    This function may stream if:
      - inbound Accept includes text/event-stream, OR
      - json_body contains {"stream": true}
    """
    settings = get_settings()
    method_u = method.upper()
    url = build_upstream_url(path, request=request, query=query)

    headers = build_outbound_headers(inbound_headers or {}, path_hint=path)
    timeout_s = _get_timeout_seconds(settings)

    body_bytes: bytes = b""
    content_type = headers.get("Content-Type") or headers.get("content-type")

    if json_body is not None:
        body_bytes = json.dumps(json_body).encode("utf-8")
        # Ensure content-type for JSON bodies (unless caller already set it).
        if not content_type:
            headers["Content-Type"] = "application/json"
            content_type = "application/json"

    accept = (headers.get("Accept") or headers.get("accept") or "")
    wants_stream = _detect_wants_stream(
        accept_header=accept,
        content_type=content_type,
        body_bytes=body_bytes,
    )

    client = get_async_httpx_client()

    if wants_stream:
        upstream_cm = client.stream(method_u, url, headers=headers, content=body_bytes, timeout=timeout_s)
        upstream_resp = await upstream_cm.__aenter__()

        async def _iter() -> Any:
            try:
                async for chunk in upstream_resp.aiter_bytes():
                    yield chunk
            finally:
                await upstream_cm.__aexit__(None, None, None)

        media_type = upstream_resp.headers.get("content-type") or "text/event-stream"
        return StreamingResponse(
            _iter(),
            status_code=upstream_resp.status_code,
            headers=_filter_response_headers(upstream_resp.headers),
            media_type=media_type,
        )

    try:
        upstream_resp = await client.request(
            method_u,
            url,
            headers=headers,
            content=body_bytes,
            timeout=timeout_s,
        )
    except httpx.HTTPError as e:
        raise HTTPException(status_code=424, detail=f"Upstream request failed: {type(e).__name__}: {e}") from e

    return Response(
        content=upstream_resp.content,
        status_code=upstream_resp.status_code,
        headers=_filter_response_headers(upstream_resp.headers),
        media_type=upstream_resp.headers.get("content-type"),
    )


async def forward_embeddings_create(
    body: Dict[str, Any],
    *,
    inbound_headers: Optional[Mapping[str, str]] = None,
) -> Dict[str, Any]:
    """
    Convenience helper used by /v1/embeddings route.

    Returns JSON dict; raises HTTPException on upstream transport failures.
    """
    settings = get_settings()
    headers = build_outbound_headers(inbound_headers or {}, path_hint="/v1/embeddings")
    headers.setdefault("Content-Type", "application/json")

    client = get_async_httpx_client()
    timeout_s = _get_timeout_seconds(settings)

    try:
        resp = await client.post(url, headers=headers, json=body, timeout=timeout_s)
    except httpx.HTTPError as e:
        raise HTTPException(status_code=424, detail=f"Upstream request failed: {type(e).__name__}: {e}") from e

    # Even for non-2xx, OpenAI returns JSON error bodies; pass through as dict when possible.
    try:
        return resp.json()
    except Exception:
        return {"status_code": resp.status_code, "body": resp.text}


# Back-compat/private aliases referenced by older SSE wiring (avoid import-time crashes).
_build_outbound_headers = build_outbound_headers
_filter_response_headers = _filter_response_headers
_join_upstream_url = _join_upstream_url
_join_upstream_url_compat = _join_upstream_url_compat
