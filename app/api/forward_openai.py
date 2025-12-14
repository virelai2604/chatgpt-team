from __future__ import annotations

from typing import Any, Dict, Mapping, Optional

import httpx
from fastapi import Request, Response

from app.core.config import get_settings
from app.core.http_client import get_async_httpx_client, get_async_openai_client

# RFC 7230 hop-by-hop headers that must not be forwarded.
_HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
}


def normalize_base_url(base_url: str) -> str:
    """
    Normalize an upstream OpenAI base URL.

    The relay supports OPENAI_API_BASE with or without a trailing `/v1`.
    Internally, we normalize to the host root (no trailing slash, no `/v1`),
    and then build_upstream_url() always ensures the request path includes `/v1/...`.
    """
    normalized = (base_url or "").rstrip("/")
    if normalized.endswith("/v1"):
        normalized = normalized[:-3]
    return normalized


def normalize_upstream_path(path: str) -> str:
    """
    Ensure the path is an absolute upstream OpenAI path under `/v1`.

    Examples:
      - "v1/models"         -> "/v1/models"
      - "/v1/models"        -> "/v1/models"
      - "/models"           -> "/v1/models"
      - "/v1"               -> "/v1"
    """
    if not path:
        return "/v1/"

    if not path.startswith("/"):
        path = "/" + path

    if path == "/v1":
        return path

    if path.startswith("/v1/"):
        return path

    # Any other absolute path is treated as relative to /v1
    return "/v1" + path


def build_upstream_url(path: str) -> str:
    """
    Build the full upstream URL to OpenAI from a path.
    """
    settings = get_settings()
    base = normalize_base_url(settings.openai_base_url)
    upstream_path = normalize_upstream_path(path)
    return f"{base}{upstream_path}"


def filter_upstream_headers(headers: Mapping[str, str]) -> Dict[str, str]:
    """
    Filter upstream response headers so we don't forward hop-by-hop headers.
    """
    return {
        k: v for k, v in headers.items() if k.lower() not in _HOP_BY_HOP_HEADERS
    }


def _header_get(headers: Mapping[str, str], name: str) -> Optional[str]:
    """
    Best-effort case-insensitive header lookup that works for both dict-like objects
    and Starlette Headers (which are already case-insensitive).
    """
    if not headers:
        return None
    return (
        headers.get(name)  # type: ignore[arg-type]
        or headers.get(name.lower())  # type: ignore[arg-type]
        or headers.get(name.title())  # type: ignore[arg-type]
    )


def build_outbound_headers(
    in_headers: Mapping[str, str],
    *,
    content_type: Optional[str] = None,
    default_json: bool = True,
    forward_accept: bool = True,
    extra_headers: Optional[Mapping[str, str]] = None,
) -> Dict[str, str]:
    """
    Build outbound headers for upstream OpenAI calls.

    - Always inject Authorization from server-side settings (do not forward user auth).
    - Optionally forward OpenAI-Beta and Idempotency-Key if present.
    - Optionally set Content-Type; if not set and default_json=True, defaults to application/json.
    """
    settings = get_settings()

    headers: Dict[str, str] = {"Authorization": f"Bearer {settings.openai_api_key}"}

    if settings.openai_organization:
        headers["OpenAI-Organization"] = settings.openai_organization
    if settings.openai_project:
        headers["OpenAI-Project"] = settings.openai_project

    beta = _header_get(in_headers, "OpenAI-Beta") or settings.openai_beta
    if beta:
        headers["OpenAI-Beta"] = beta

    idem = _header_get(in_headers, "Idempotency-Key")
    if idem:
        headers["Idempotency-Key"] = idem

    if forward_accept:
        accept = _header_get(in_headers, "Accept")
        if accept:
            headers["Accept"] = accept

    if content_type is not None:
        headers["Content-Type"] = content_type
    else:
        inbound_ct = _header_get(in_headers, "Content-Type")
        if inbound_ct:
            headers["Content-Type"] = inbound_ct
        elif default_json:
            headers["Content-Type"] = "application/json"

    if extra_headers:
        for k, v in extra_headers.items():
            if v is None:
                continue
            headers[k] = v

    return headers


def _normalize_query_params(
    query: Optional[Mapping[str, Any]],
) -> Optional[Dict[str, Any]]:
    """
    Normalize query params for httpx:
    - Drop None values
    - Convert booleans to 'true'/'false' (OpenAI conventions)
    """
    if not query:
        return None
    out: Dict[str, Any] = {}
    for k, v in query.items():
        if v is None:
            continue
        if isinstance(v, bool):
            out[k] = "true" if v else "false"
        else:
            out[k] = v
    return out or None


async def forward_openai_request(request: Request) -> Response:
    """
    Generic pass-through for endpoints already mounted in this relay.

    It forwards the incoming request method/path/query/body to upstream OpenAI,
    injecting server-side auth headers.
    """
    settings = get_settings()

    incoming_path = request.url.path.lstrip("/")  # e.g. "v1/batches" or "vector_stores"
    url = build_upstream_url("/" + incoming_path)

    headers = build_outbound_headers(
        request.headers,
        content_type=None,
        default_json=True,
        forward_accept=True,
    )

    body = await request.body()
    client = get_async_httpx_client()

    resp = await client.request(
        method=request.method,
        url=url,
        params=request.query_params,
        headers=headers,
        content=body if body else None,
        timeout=settings.proxy_timeout_seconds,
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
    query: Optional[Mapping[str, Any]] = None,
    json_body: Any = None,
    inbound_headers: Optional[Mapping[str, str]] = None,
) -> Response:
    """
    Forward an arbitrary upstream OpenAI request specified by method + path.

    This exists primarily for the Option A `/v1/proxy` envelope, where the inbound
    request path is always `/v1/proxy`, but the user intends to call another upstream route.
    """
    settings = get_settings()

    upstream_url = build_upstream_url(path)
    headers = build_outbound_headers(
        inbound_headers or {},
        content_type="application/json" if json_body is not None else None,
        default_json=json_body is not None,
        forward_accept=True,
    )

    client = get_async_httpx_client()
    resp = await client.request(
        method=method.upper(),
        url=upstream_url,
        params=_normalize_query_params(query),
        headers=headers,
        json=json_body if json_body is not None else None,
        timeout=settings.proxy_timeout_seconds,
    )

    return Response(
        content=resp.content,
        status_code=resp.status_code,
        headers=filter_upstream_headers(resp.headers),
        media_type=resp.headers.get("content-type"),
    )


async def forward_responses_create(body: Dict[str, Any]) -> Dict[str, Any]:
    client = get_async_openai_client()
    result = await client.responses.create(**body)
    return result.model_dump()


async def forward_embeddings_create(body: Dict[str, Any]) -> Dict[str, Any]:
    client = get_async_openai_client()
    result = await client.embeddings.create(**body)
    return result.model_dump()


async def forward_models_list() -> Dict[str, Any]:
    client = get_async_openai_client()
    result = await client.models.list()
    return result.model_dump()


async def forward_models_retrieve(model: str) -> Dict[str, Any]:
    client = get_async_openai_client()
    result = await client.models.retrieve(model)
    return result.model_dump()
