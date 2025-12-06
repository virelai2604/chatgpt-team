# app/api/forward_openai.py

from __future__ import annotations

from typing import Any, Dict

import httpx
from fastapi import Request, Response

from app.core.config import get_settings
from app.core.http_client import get_async_openai_client
from app.utils.logger import get_logger

logger = get_logger(__name__)
_settings = get_settings()


def _to_plain(result: Any) -> Any:
    """
    Convert OpenAI SDK result objects into JSON-serializable dicts when possible.

    Newer SDK responses are Pydantic v2 models; older ones may expose `to_dict`.
    If neither works we return the object and let FastAPI handle serialization.
    """
    # Pydantic v2-style
    if hasattr(result, "model_dump"):
        try:
            return result.model_dump()
        except TypeError:
            # Some objects may not support model_dump with no args
            pass

    # Older-style helper
    if hasattr(result, "to_dict"):
        try:
            return result.to_dict()
        except TypeError:
            pass

    # Fall back to returning the object; FastAPI may know how to serialize it.
    return result


# ---------------------------------------------------------------------------
# Typed SDK-based helpers (Responses / Embeddings / Images / Videos / Models)
# ---------------------------------------------------------------------------


async def forward_responses_create(payload: Dict[str, Any]) -> Any:
    """
    Forward to OpenAI Responses API (primary text / multimodal entry point).

    Equivalent to:
        client.responses.create(**payload)
    """
    client = get_async_openai_client()
    logger.debug("Forwarding /v1/responses payload: %s", payload)
    result = await client.responses.create(**payload)
    return _to_plain(result)


async def forward_embeddings_create(payload: Dict[str, Any]) -> Any:
    """
    Forward to OpenAI Embeddings API.

    Equivalent to:
        client.embeddings.create(**payload)
    """
    client = get_async_openai_client()
    logger.debug("Forwarding /v1/embeddings payload: %s", payload)
    result = await client.embeddings.create(**payload)
    return _to_plain(result)


async def forward_images_generate(payload: Dict[str, Any]) -> Any:
    """
    Forward to OpenAI Images API.

    Equivalent to:
        client.images.generate(**payload)
    """
    client = get_async_openai_client()
    logger.debug("Forwarding /v1/images payload: %s", payload)
    result = await client.images.generate(**payload)
    return _to_plain(result)


async def forward_videos_create(payload: Dict[str, Any]) -> Any:
    """
    Forward to OpenAI Videos API.

    Equivalent to:
        client.videos.create(**payload)
    """
    client = get_async_openai_client()
    logger.debug("Forwarding /v1/videos payload: %s", payload)
    result = await client.videos.create(**payload)
    return _to_plain(result)


async def forward_models_list() -> Any:
    """
    Forward to OpenAI Models API (list all models).

    Equivalent to:
        client.models.list()
    """
    client = get_async_openai_client()
    logger.debug("Forwarding /v1/models list")
    result = await client.models.list()
    return _to_plain(result)


async def forward_models_retrieve(model_id: str) -> Any:
    """
    Forward to OpenAI Models API (retrieve a single model).

    Equivalent to:
        client.models.retrieve(model_id)
    """
    client = get_async_openai_client()
    logger.debug("Forwarding /v1/models/%s retrieve", model_id)
    result = await client.models.retrieve(model_id)
    return _to_plain(result)


# ---------------------------------------------------------------------------
# Generic catch‑all proxy for /v1/* subroutes
# Used by app/routes/files.py, batches.py, containers.py, etc.
# ---------------------------------------------------------------------------


async def _forward_to_openai(request: Request, path: str) -> Response:
    """
    Low-level HTTP proxy to the OpenAI REST API using the configured settings.

    Args:
        request: Incoming FastAPI Request.
        path: Path under the upstream base (e.g. "files", "files/123/content").
    """
    # Build upstream URL; base is typically https://api.openai.com/v1
    base = _settings.openai_base_url.rstrip("/")
    url = f"{base}/{path.lstrip('/')}"
    params: Dict[str, str] = dict(request.query_params)

    # Copy headers but drop hop-by-hop headers and host/content-length
    incoming_headers = dict(request.headers)
    for hop in (
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
    ):
        incoming_headers.pop(hop, None)

    headers: Dict[str, str] = {
        **incoming_headers,
        "Authorization": f"Bearer {_settings.openai_api_key}",
    }

    if _settings.openai_organization:
        headers["OpenAI-Organization"] = _settings.openai_organization

    body = await request.body()

    timeout = getattr(_settings, "timeout_seconds", None)
    async with httpx.AsyncClient(timeout=timeout or 20.0) as client:
        upstream = await client.request(
            method=request.method,
            url=url,
            params=params,
            headers=headers,
            content=body or None,
        )

    logger.debug(
        "Forwarded request to OpenAI",
        extra={
            "method": request.method,
            "path": path,
            "status_code": upstream.status_code,
        },
    )

    # Filter response headers to avoid conflicts with FastAPI/Uvicorn
    response_headers = {
        k: v
        for k, v in upstream.headers.items()
        if k.lower() in {"content-type", "cache-control"}
    }

    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        headers=response_headers,
        media_type=upstream.headers.get("content-type"),
    )


def _extract_upstream_path(request: Request) -> str:
    """
    Translate the relay path (e.g. `/v1/files/abc`) into the upstream path
    relative to OPENAI_BASE_URL.

    If OPENAI_BASE_URL already ends with `/v1`, we strip the `/v1/` prefix
    from the incoming path so we don't double it.
    """
    raw_path = request.url.path  # e.g. "/v1/files/abc"
    # Normalise and remove leading slash
    path = raw_path.lstrip("/")  # "v1/files/abc" or "files/abc"

    # If our base already includes /v1, drop leading "v1/" from the path.
    base = _settings.openai_base_url.rstrip("/")
    if base.endswith("/v1") and path.startswith("v1/"):
        path = path[len("v1/") :]

    return path


async def forward_openai_request(request: Request) -> Response:
    """
    Generic pass-through for OpenAI's REST API under /v1/*.

    Used by:
      - app/routes/files.py
      - app/routes/batches.py
      - app/routes/containers.py
      - app/routes/conversations.py
      - app/routes/vector_stores.py
      - and any other future /v1/* route families.

    This keeps all subroutes on the same config-driven HTTP proxy while
    the main, high-traffic endpoints use the typed SDK helpers above.
    """
    path = _extract_upstream_path(request)
    return await _forward_to_openai(request, path)
