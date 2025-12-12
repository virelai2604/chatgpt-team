from __future__ import annotations

import json
from typing import Any, Dict, Optional, Tuple

from fastapi import Request
from fastapi.responses import Response as FastAPIResponse
from starlette.datastructures import Headers

from app.core.config import settings
from app.core.http_client import get_async_httpx_client, get_async_openai_client
from app.utils.logger import get_logger

logger = get_logger(__name__)


def _normalized_upstream_base(base_url: str) -> str:
    """
    For raw HTTP forwarding we want the *root* host without a duplicated /v1.
    Accept:
      - https://api.openai.com
      - https://api.openai.com/v1
    Normalize to:
      - https://api.openai.com
    """
    b = base_url.rstrip("/")
    if b.endswith("/v1"):
        b = b[:-3]
    return b


def build_upstream_url(path: str) -> str:
    """
    path should be like '/v1/responses' or '/v1/responses/compact'.
    """
    if not path.startswith("/"):
        path = "/" + path
    base = _normalized_upstream_base(str(settings.openai_base_url))
    return f"{base}{path}"


def _filtered_upstream_headers(upstream_headers: Headers) -> Dict[str, str]:
    # Avoid hop-by-hop headers; keep content-type and any request IDs.
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
        lk = k.lower()
        if lk in drop:
            continue
        out[k] = v
    return out


def _outbound_headers(in_headers: Headers) -> Dict[str, str]:
    """
    Build headers for upstream OpenAI call.
    We do NOT forward the incoming Authorization; we use the server key.
    """
    headers: Dict[str, str] = {
        "Authorization": f"Bearer {settings.openai_api_key}",
    }
    # Preserve content-type if provided.
    if "content-type" in in_headers:
        headers["Content-Type"] = in_headers["content-type"]
    else:
        headers["Content-Type"] = "application/json"

    # Optional passthrough for organization/project headers if present.
    for h in ("OpenAI-Organization", "OpenAI-Project"):
        if h.lower() in in_headers:
            headers[h] = in_headers[h.lower()]

    return headers


async def forward_openai_request(request: Request) -> FastAPIResponse:
    """
    Generic JSON pass-through to the OpenAI upstream.

    Fixes:
      - Avoid /v1/v1 duplication by normalizing base url.
      - Use per-event-loop httpx client to avoid 'Event loop is closed' under pytest. 
    """
    method = request.method.upper()
    path = request.url.path  # e.g. /v1/responses/compact
    url = build_upstream_url(path)

    body = await request.body()
    params = dict(request.query_params)

    client = get_async_httpx_client()
    resp = await client.request(
        method=method,
        url=url,
        headers=_outbound_headers(request.headers),
        params=params,
        content=body if body else None,
    )

    return FastAPIResponse(
        content=resp.content,
        status_code=resp.status_code,
        headers=_filtered_upstream_headers(resp.headers),
        media_type=resp.headers.get("content-type"),
    )


# --- Typed helpers used by your routes (keeps existing imports working) ---

async def forward_responses_create(payload: Dict[str, Any]) -> Any:
    client = get_async_openai_client()
    return await client.responses.create(**payload)


async def forward_embeddings_create(payload: Dict[str, Any]) -> Any:
    client = get_async_openai_client()
    return await client.embeddings.create(**payload)


async def forward_models_list() -> Any:
    client = get_async_openai_client()
    return await client.models.list()


async def forward_models_retrieve(model: str) -> Any:
    client = get_async_openai_client()
    return await client.models.retrieve(model)
