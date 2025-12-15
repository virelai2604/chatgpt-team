from __future__ import annotations

from typing import Any, Dict, Mapping, Optional

import httpx
from fastapi import HTTPException, Request
from fastapi.responses import Response

from app.core.http_client import get_async_httpx_client, get_async_openai_client
from app.utils.logger import relay_log

# Compatibility: support either `get_settings()` or a module-level `settings`
try:
    from app.core.config import get_settings  # type: ignore
except ImportError:  # pragma: no cover
    from app.core.config import settings as _settings  # type: ignore

    def get_settings():  # type: ignore
        return _settings


# -------------------------
# URL + header utilities
# -------------------------

def normalize_base_url(base_url: str) -> str:
    """
    Normalize an OpenAI base URL to *not* end with /v1 and *not* have a trailing slash.

    Examples:
      - https://api.openai.com/v1   -> https://api.openai.com
      - https://api.openai.com/v1/  -> https://api.openai.com
      - https://api.openai.com/     -> https://api.openai.com
    """
    if not base_url:
        return "https://api.openai.com"

    base = base_url.strip()
    while base.endswith("/"):
        base = base[:-1]

    if base.endswith("/v1"):
        base = base[:-3]
        while base.endswith("/"):
            base = base[:-1]
    return base


def normalize_upstream_path(path: str) -> str:
    """
    Ensure an upstream OpenAI path is normalized for API calls.

    - Always starts with "/"
    - If it looks like a first-class OpenAI resource path (files, responses, etc)
      and does not start with "/v1/", prefix it with "/v1".
    """
    if not path:
        return "/v1"

    p = path.strip()
    if not p.startswith("/"):
        p = "/" + p

    if p.startswith("/v1/") or p == "/v1":
        return p

    v1_roots = (
        "/models",
        "/embeddings",
        "/responses",
        "/files",
        "/vector_stores",
        "/containers",
        "/conversations",
        "/batches",
        "/images",
        "/videos",
        "/audio",
        "/realtime",
        "/moderations",
        "/uploads",
    )
    if p.startswith(v1_roots):
        return "/v1" + p

    return p


def build_upstream_url(path: str) -> str:
    settings = get_settings()
    base = normalize_base_url(getattr(settings, "openai_base_url", "https://api.openai.com"))
    return base + normalize_upstream_path(path)


def _get_timeout_seconds() -> float:
    """
    Compatibility shim:
    - Newer versions used proxy_timeout_seconds.
    - Older versions used PROXY_TIMEOUT / RELAY_TIMEOUT.
    """
    settings = get_settings()
    for attr in ("proxy_timeout_seconds", "PROXY_TIMEOUT", "HTTP_TIMEOUT_SECONDS", "RELAY_TIMEOUT", "timeout_seconds"):
        if hasattr(settings, attr):
            try:
                val = float(getattr(settings, attr))
                if val > 0:
                    return val
            except Exception:
                continue
    return 90.0


def _normalize_query_params(query: Optional[Mapping[str, Any]]) -> Optional[Dict[str, Any]]:
    if not query:
        return None
    return dict(query)


def build_outbound_headers(
    *,
    inbound_headers: Optional[Mapping[str, str]] = None,
    content_type: Optional[str] = None,
    forward_accept: bool = True,
    path_hint: Optional[str] = None,
) -> Dict[str, str]:
    """
    Build headers for upstream OpenAI calls.

    - Never forwards incoming Authorization (relay token).
    - Sets upstream Authorization = OPENAI_API_KEY.
    - Forwards a limited set of safe headers (Accept, Content-Type, Idempotency-Key).
    - Adds OpenAI-Organization / OpenAI-Project if configured.
    - Adds OpenAI-Beta for beta endpoints when configured.
    """
    settings = get_settings()
    if not getattr(settings, "openai_api_key", None):
        raise HTTPException(status_code=500, detail="Server misconfigured: OPENAI_API_KEY is not set")

    out: Dict[str, str] = {"Authorization": f"Bearer {settings.openai_api_key}"}

    org = getattr(settings, "openai_organization", None)
    if org:
        out["OpenAI-Organization"] = org
    proj = getattr(settings, "openai_project", None)
    if proj:
        out["OpenAI-Project"] = proj

    beta = getattr(settings, "openai_beta", None)
    hint = path_hint or ""
    if beta and (
        hint.startswith("/v1/vector_stores")
        or hint.startswith("/v1/containers")
        or hint.startswith("/v1/conversations")
    ):
        out["OpenAI-Beta"] = beta

    if inbound_headers:
        if forward_accept:
            accept = inbound_headers.get("accept")
            if accept:
                out["Accept"] = accept

        ct = content_type or inbound_headers.get("content-type")
        if ct:
            out["Content-Type"] = ct

        idem = inbound_headers.get("idempotency-key")
        if idem:
            out["Idempotency-Key"] = idem

        rid = inbound_headers.get("x-request-id")
        if rid:
            out["X-Request-Id"] = rid

    return out


def filter_upstream_headers(headers: Mapping[str, str]) -> Dict[str, str]:
    """
    Filter upstream headers to a safe subset to return to clients.
    Avoid forwarding hop-by-hop headers and content-encoding (httpx may decompress).
    """
    allow = {
        "content-type",
        "content-length",
        "content-disposition",
        "cache-control",
        "etag",
        "last-modified",
        "accept-ranges",
        "content-range",
        "x-request-id",
        "openai-processing-ms",
        "x-ratelimit-limit-requests",
        "x-ratelimit-remaining-requests",
        "x-ratelimit-reset-requests",
        "x-ratelimit-limit-tokens",
        "x-ratelimit-remaining-tokens",
        "x-ratelimit-reset-tokens",
    }
    out: Dict[str, str] = {}
    for k, v in headers.items():
        lk = k.lower()
        if lk in allow:
            out[k] = v
    return out


def _maybe_model_dump(obj: Any) -> Any:
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if hasattr(obj, "dict"):
        return obj.dict()
    return obj


# -------------------------
# Generic forwarders
# -------------------------

async def forward_openai_method_path(
    *,
    method: str,
    path: str,
    query: Optional[Mapping[str, Any]] = None,
    json_body: Optional[Any] = None,
    inbound_headers: Optional[Mapping[str, str]] = None,
) -> Response:
    """
    Forward an OpenAI API call by method + path.

    Used by /v1/proxy and some explicit JSON endpoints.

    Key behavior:
      - Does NOT raise on non-2xx; passes upstream status/body back to caller.
      - Raises 502/504 only on network/timeout errors.
    """
    upstream_path = normalize_upstream_path(path)
    upstream_url = build_upstream_url(upstream_path)

    content_type = "application/json" if json_body is not None else None
    headers = build_outbound_headers(
        inbound_headers=inbound_headers,
        content_type=content_type,
        path_hint=upstream_path,
    )

    client = get_async_httpx_client()
    timeout = _get_timeout_seconds()

    try:
        resp = await client.request(
            method=method.upper(),
            url=upstream_url,
            params=_normalize_query_params(query),
            headers=headers,
            json=json_body if json_body is not None else None,
            timeout=timeout,
            follow_redirects=True,
        )
    except httpx.TimeoutException as exc:
        relay_log.warning("Upstream timeout: %s %s (%s)", method.upper(), upstream_url, type(exc).__name__)
        raise HTTPException(
            status_code=504,
            detail=f"Upstream timeout calling {method.upper()} {upstream_url}: {type(exc).__name__}: {exc}",
        ) from exc
    except httpx.RequestError as exc:
        relay_log.warning("Upstream request error: %s %s (%s)", method.upper(), upstream_url, type(exc).__name__)
        raise HTTPException(
            status_code=502,
            detail=f"Upstream request failed calling {method.upper()} {upstream_url}: {type(exc).__name__}: {exc}",
        ) from exc

    return Response(
        content=resp.content,
        status_code=resp.status_code,
        headers=filter_upstream_headers(resp.headers),
        media_type=resp.headers.get("content-type"),
    )


async def forward_openai_request(request: Request) -> Response:
    """
    Forward an incoming FastAPI Request to upstream OpenAI preserving raw body bytes.

    NOTE: This is suitable for JSON endpoints and small binary payloads.
    For large binary downloads use a StreamingResponse in the route.
    """
    upstream_path = normalize_upstream_path(request.url.path)
    upstream_url = build_upstream_url(upstream_path)

    body = await request.body()
    content_type = request.headers.get("content-type")
    headers = build_outbound_headers(
        inbound_headers=request.headers,
        content_type=content_type,
        path_hint=upstream_path,
    )

    client = get_async_httpx_client()
    timeout = _get_timeout_seconds()

    try:
        resp = await client.request(
            method=request.method,
            url=upstream_url,
            params=request.query_params,
            headers=headers,
            content=body if body else None,
            timeout=timeout,
            follow_redirects=True,
        )
    except httpx.TimeoutException as exc:
        relay_log.warning("Upstream timeout: %s %s (%s)", request.method, upstream_url, type(exc).__name__)
        raise HTTPException(
            status_code=504,
            detail=f"Upstream timeout calling {request.method} {upstream_url}: {type(exc).__name__}: {exc}",
        ) from exc
    except httpx.RequestError as exc:
        relay_log.warning("Upstream request error: %s %s (%s)", request.method, upstream_url, type(exc).__name__)
        raise HTTPException(
            status_code=502,
            detail=f"Upstream request failed calling {request.method} {upstream_url}: {type(exc).__name__}: {exc}",
        ) from exc

    return Response(
        content=resp.content,
        status_code=resp.status_code,
        headers=filter_upstream_headers(resp.headers),
        media_type=resp.headers.get("content-type"),
    )


# -------------------------
# Typed helpers (SDK-based)
# -------------------------

async def forward_models_list() -> Any:
    client = get_async_openai_client()
    result = await client.models.list()
    return _maybe_model_dump(result)


async def forward_embeddings_create(body: Dict[str, Any]) -> Any:
    client = get_async_openai_client()
    result = await client.embeddings.create(**body)
    return _maybe_model_dump(result)


async def forward_responses_create(body: Dict[str, Any]) -> Any:
    client = get_async_openai_client()
    result = await client.responses.create(**body)
    return _maybe_model_dump(result)


async def forward_files_list(*, purpose: Optional[str] = None) -> Any:
    client = get_async_openai_client()
    if purpose:
        result = await client.files.list(purpose=purpose)
    else:
        result = await client.files.list()
    return _maybe_model_dump(result)


async def forward_files_retrieve(file_id: str) -> Any:
    client = get_async_openai_client()
    result = await client.files.retrieve(file_id)
    return _maybe_model_dump(result)


async def forward_files_delete(file_id: str) -> Any:
    client = get_async_openai_client()
    result = await client.files.delete(file_id)
    return _maybe_model_dump(result)


async def forward_files_create(*, file: Any, purpose: str) -> Any:
    client = get_async_openai_client()

    filename = getattr(file, "filename", "upload.bin")
    content_type = getattr(file, "content_type", "application/octet-stream")

    read = getattr(file, "read", None)
    if not callable(read):
        raise HTTPException(status_code=400, detail="Invalid upload: 'file' is missing a .read() method")

    maybe = read()
    data: bytes = await maybe if hasattr(maybe, "__await__") else maybe  # type: ignore

    result = await client.files.create(file=(filename, data, content_type), purpose=purpose)
    return _maybe_model_dump(result)
