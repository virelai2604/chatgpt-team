from __future__ import annotations

from typing import Any, Dict, Mapping, Optional

import httpx
from fastapi import HTTPException, Request, Response

from app.core.config import get_settings
from app.core.http_client import get_async_httpx_client, get_async_openai_client

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
    normalized = (base_url or "").rstrip("/")
    if normalized.endswith("/v1"):
        normalized = normalized[:-3]
    return normalized


def normalize_upstream_path(path: str) -> str:
    if not path:
        return "/v1/"

    if not path.startswith("/"):
        path = "/" + path

    if path == "/v1":
        return path

    if path.startswith("/v1/"):
        return path

    return "/v1" + path


def build_upstream_url(path: str) -> str:
    settings = get_settings()
    base = normalize_base_url(settings.openai_base_url)
    upstream_path = normalize_upstream_path(path)
    return f"{base}{upstream_path}"


def filter_upstream_headers(headers: Mapping[str, str]) -> Dict[str, str]:
    return {k: v for k, v in headers.items() if k.lower() not in _HOP_BY_HOP_HEADERS}


def _header_get(headers: Mapping[str, str], name: str) -> Optional[str]:
    if not headers:
        return None
    return (
        headers.get(name)  # type: ignore[arg-type]
        or headers.get(name.lower())  # type: ignore[arg-type]
        or headers.get(name.title())  # type: ignore[arg-type]
    )


def _select_beta(path_hint: str | None) -> Optional[str]:
    s = get_settings()
    p = (path_hint or "").strip()

    # Honor explicit OPENAI_BETA if you set it.
    if s.openai_beta:
        return s.openai_beta

    # Apply targeted beta headers by surface.
    if p.startswith("/v1/realtime") and s.openai_realtime_beta:
        return s.openai_realtime_beta

    # Assistants-adjacent surfaces (vector stores, etc.) may require assistants=v2.
    if (
        (p.startswith("/v1/assistants") or p.startswith("/v1/threads") or p.startswith("/v1/vector_stores"))
        and s.openai_assistants_beta
    ):
        return s.openai_assistants_beta

    return None


def build_outbound_headers(
    in_headers: Mapping[str, str],
    *,
    content_type: Optional[str] = None,
    default_json: bool = True,
    forward_accept: bool = True,
    path_hint: Optional[str] = None,
    extra_headers: Optional[Mapping[str, str]] = None,
) -> Dict[str, str]:
    settings = get_settings()

    headers: Dict[str, str] = {"Authorization": f"Bearer {settings.openai_api_key}"}

    if settings.openai_organization:
        headers["OpenAI-Organization"] = settings.openai_organization
    if settings.openai_project:
        headers["OpenAI-Project"] = settings.openai_project

    beta = _header_get(in_headers, "OpenAI-Beta") or _select_beta(path_hint)
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
            if v is not None:
                headers[k] = v

    return headers


def _normalize_query_params(query: Optional[Mapping[str, Any]]) -> Optional[Dict[str, Any]]:
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
    settings = get_settings()
    if not settings.openai_api_key:
        raise HTTPException(status_code=500, detail="Server misconfigured: OPENAI_API_KEY is not set")

    upstream_url = build_upstream_url(request.url.path)

    default_json = request.method not in {"GET", "HEAD"}  # don't force CT for GETs
    headers = build_outbound_headers(
        request.headers,
        content_type=None,
        default_json=default_json,
        forward_accept=True,
        path_hint=request.url.path,
    )

    body = await request.body()
    client = get_async_httpx_client()

    resp = await client.request(
        method=request.method,
        url=upstream_url,
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
    settings = get_settings()
    if not settings.openai_api_key:
        raise HTTPException(status_code=500, detail="Server misconfigured: OPENAI_API_KEY is not set")

    upstream_url = build_upstream_url(path)
    headers = build_outbound_headers(
        inbound_headers or {},
        content_type="application/json" if json_body is not None else None,
        default_json=json_body is not None,
        forward_accept=True,
        path_hint=path,
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


# Typed helpers (used by some explicit routes)
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
