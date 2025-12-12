# app/api/forward_openai.py
from __future__ import annotations

import json
from typing import Any, Dict

from fastapi import Request
from fastapi.responses import Response as FastAPIResponse

from app.core.config import settings
from app.core.http_client import get_async_httpx_client, get_async_openai_client
from app.utils.logger import get_logger

logger = get_logger(__name__)


_HOP_BY_HOP = {
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


def _join_openai_url(base: str, path: str, query: str | None = None) -> str:
    """
    Join base + path while avoiding double /v1 when:
      base == https://api.openai.com/v1
      path == /v1/responses
    """
    base = (base or "").rstrip("/")
    path = "/" + (path or "").lstrip("/")

    if base.endswith("/v1") and path.startswith("/v1/"):
        # remove the extra '/v1' from the path
        path = path[3:]  # keeps the leading '/'

    url = f"{base}{path}"
    if query:
        url = f"{url}?{query.lstrip('?')}"
    return url


def _proxy_headers(in_headers: dict[str, str]) -> dict[str, str]:
    headers: dict[str, str] = {}
    for k, v in in_headers.items():
        if k.lower() in _HOP_BY_HOP:
            continue
        headers[k] = v

    # Always use server-side OpenAI key upstream
    headers["Authorization"] = f"Bearer {settings.openai_api_key}"
    return headers


async def forward_openai_request(request: Request) -> FastAPIResponse:
    """
    Generic HTTP pass-through to OpenAI upstream for /v1/* endpoints.
    (Non-streaming use-cases.)
    """
    client = get_async_httpx_client()

    upstream_url = _join_openai_url(
        settings.openai_base_url,
        request.url.path,
        request.url.query if request.url.query else None,
    )

    body = await request.body()
    headers = _proxy_headers(dict(request.headers))

    upstream = await client.request(
        request.method,
        upstream_url,
        headers=headers,
        content=body if body else None,
    )

    # Copy response headers back (minus hop-by-hop-ish headers)
    out_headers: dict[str, str] = {}
    for k, v in upstream.headers.items():
        lk = k.lower()
        if lk in {"content-encoding", "transfer-encoding", "connection", "keep-alive"}:
            continue
        out_headers[k] = v

    media_type = upstream.headers.get("content-type")
    return FastAPIResponse(
        content=upstream.content,
        status_code=upstream.status_code,
        media_type=media_type,
        headers=out_headers,
    )


async def forward_responses_create(body: Dict[str, Any]) -> Any:
    """
    SDK-driven /v1/responses create. If body['stream']=True, the SDK returns an AsyncStream.
    """
    client = get_async_openai_client()
    return await client.responses.create(**body)
