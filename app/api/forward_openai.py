# app/api/forward_openai.py

from __future__ import annotations

from typing import Any, Dict, Optional
from urllib.parse import urljoin

import httpx
from fastapi import Request, Response
from starlette.status import HTTP_502_BAD_GATEWAY

from app.core.config import settings
from app.core.http_client import get_async_openai_client, get_openai_client
from app.utils.logger import get_logger

logger = get_logger(__name__)


# --- Typed helpers for common high-traffic endpoints -------------------------


async def forward_responses_create(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Use the OpenAI Python SDK to call the Responses API.

    This is the "canonical" way to talk to the API and should be preferred
    for most traffic.
    """
    client = get_async_openai_client()
    # We assume the payload is already a valid Responses.create() payload.
    resp = await client.responses.create(**payload)
    return resp.model_dump()


async def forward_embeddings_create(payload: Dict[str, Any]) -> Dict[str, Any]:
    client = get_async_openai_client()
    resp = await client.embeddings.create(**payload)
    return resp.model_dump()


async def forward_images_generate(payload: Dict[str, Any]) -> Dict[str, Any]:
    client = get_async_openai_client()
    resp = await client.images.generate(**payload)
    return resp.model_dump()


async def forward_videos_create(payload: Dict[str, Any]) -> Dict[str, Any]:
    client = get_async_openai_client()
    resp = await client.videos.generate(**payload)
    return resp.model_dump()


async def forward_models_list() -> Dict[str, Any]:
    client = get_async_openai_client()
    resp = await client.models.list()
    return resp.model_dump()


async def forward_models_retrieve(model_id: str) -> Dict[str, Any]:
    client = get_async_openai_client()
    resp = await client.models.retrieve(model_id)
    return resp.model_dump()


# --- Generic catch‑all proxy for /v1/* subroutes -----------------------------


def _extract_upstream_path(path: str) -> str:
    """
    Map the relay path to the upstream OpenAI path.

    For now we assume the relay mirrors the OpenAI URL shape under /v1.
    """
    # In the canonical relay we keep paths identical, so this is trivial.
    # Hook retained here in case we need remapping later.
    return path


async def _forward_to_openai(request: Request) -> Response:
    """
    Generic HTTP forwarder using httpx.AsyncClient.

    Used for less critical or rapidly evolving endpoints where we don't yet
    have a typed SDK wrapper.
    """
    upstream_base = settings.openai_base_url.rstrip("/")
    upstream_path = _extract_upstream_path(str(request.url.path))
    upstream_url = urljoin(f"{upstream_base}/", upstream_path.lstrip("/"))

    method = request.method.upper()
    headers = dict(request.headers)
    # Replace any incoming Authorization header with our own OpenAI key.
    headers["Authorization"] = f"Bearer {settings.openai_api_key}"

    try:
        body = await request.body()
    except Exception:  # pragma: no cover
        body = b""

    timeout = settings.timeout_seconds or 20.0

    logger.debug("Forwarding %s %s to upstream=%s", method, request.url.path, upstream_url)

    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.request(
            method=method,
            url=upstream_url,
            headers=headers,
            content=body,
        )

    # Pass through headers / status; keep body as-is.
    return Response(
        content=resp.content,
        status_code=resp.status_code,
        headers={
            k: v for k, v in resp.headers.items() if k.lower() != "content-encoding"
        },
        media_type=resp.headers.get("content-type"),
    )


async def forward_openai_request(request: Request) -> Response:
    """
    Public hook used by the route families in app/routes/*.py to forward
    arbitrary /v1/* requests we haven't explicitly wrapped yet.
    """
    try:
        return await _forward_to_openai(request)
    except Exception as exc:  # pragma: no cover
        logger.exception("Error proxying request to OpenAI: %s", exc)
        return Response(
            content=b'{"error":"upstream_error"}',
            status_code=HTTP_502_BAD_GATEWAY,
            media_type="application/json",
        )
