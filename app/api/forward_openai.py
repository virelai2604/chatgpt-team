# app/api/forward_openai.py

from __future__ import annotations

import json
import logging
from typing import Any, Dict, Mapping, Optional

import httpx
from fastapi import HTTPException
from openai import AsyncOpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------------------
# Shared AsyncOpenAI client
# --------------------------------------------------------------------------------------

_client: Optional[AsyncOpenAI] = None


def get_async_openai_client() -> AsyncOpenAI:
    """
    Lazily construct and cache a single AsyncOpenAI client for the relay.

    We respect OPENAI_API_KEY and (optionally) OPENAI_BASE_URL from settings.
    """
    global _client
    if _client is None:
        client_kwargs: Dict[str, Any] = {
            "api_key": settings.OPENAI_API_KEY,
        }
        if getattr(settings, "OPENAI_BASE_URL", None):
            client_kwargs["base_url"] = settings.OPENAI_BASE_URL

        _client = AsyncOpenAI(**client_kwargs)
        logger.info("Created AsyncOpenAI client for relay")
    return _client


def _to_plain(value: Any) -> Any:
    """
    Convert SDK types (Pydantic-style models) into plain JSON-serializable data.
    """
    if hasattr(value, "model_dump"):
        # New-style Pydantic V2 models
        return value.model_dump(mode="json")
    if hasattr(value, "to_dict"):
        # Fallback for any custom types providing to_dict()
        return value.to_dict()

    if isinstance(value, list):
        return [_to_plain(v) for v in value]
    if isinstance(value, dict):
        return {k: _to_plain(v) for k, v in value.items()}

    return value


# --------------------------------------------------------------------------------------
# Typed helpers for common endpoints
# --------------------------------------------------------------------------------------


async def forward_responses_create(data: Dict[str, Any]) -> Any:
    """
    Forward a /v1/responses *non-streaming* request through AsyncOpenAI.

    NOTE:
    - The streaming case is handled separately in the /v1/responses route
      (via SSE-style StreamingResponse).
    - If the caller passes {"stream": true} we strip it and just do a normal
      non-streaming call; the route decides whether to stream or not.
    """
    body = dict(data)  # copy so we don't mutate caller
    body.pop("stream", None)

    client = get_async_openai_client()
    logger.debug("Forwarding non-streaming /v1/responses via AsyncOpenAI: %s", body)

    try:
        resp = await client.responses.create(**body)
    except Exception as exc:  # pragma: no cover - logged and re-raised for FastAPI
        logger.exception("Error calling OpenAI Responses API", exc_info=exc)
        raise HTTPException(status_code=502, detail="Upstream OpenAI error")

    return _to_plain(resp)


async def forward_embeddings_create(data: Dict[str, Any]) -> Any:
    """
    Forward a /v1/embeddings request through AsyncOpenAI.

    We intentionally *do not* force encoding_format; the default gives a list[float]
    embedding, which matches api.openai.com and your tests.
    """
    client = get_async_openai_client()
    logger.debug("Forwarding /v1/embeddings via AsyncOpenAI: %s", data)

    try:
        resp = await client.embeddings.create(**data)
    except Exception as exc:  # pragma: no cover
        logger.exception("Error calling OpenAI Embeddings API", exc_info=exc)
        raise HTTPException(status_code=502, detail="Upstream OpenAI error")

    return _to_plain(resp)


async def forward_models_list() -> Any:
    """
    Forward GET /v1/models using AsyncOpenAI.models.list().
    """
    client = get_async_openai_client()
    logger.debug("Forwarding /v1/models (list) via AsyncOpenAI")

    try:
        resp = await client.models.list()
    except Exception as exc:  # pragma: no cover
        logger.exception("Error calling OpenAI Models list API", exc_info=exc)
        raise HTTPException(status_code=502, detail="Upstream OpenAI error")

    return _to_plain(resp)


async def forward_models_retrieve(model_id: str) -> Any:
    """
    Forward GET /v1/models/{model_id} via AsyncOpenAI.
    """
    client = get_async_openai_client()
    logger.debug("Forwarding /v1/models/%s via AsyncOpenAI", model_id)

    try:
        resp = await client.models.retrieve(model_id)
    except Exception as exc:  # pragma: no cover
        logger.exception("Error calling OpenAI Models retrieve API", exc_info=exc)
        raise HTTPException(status_code=502, detail="Upstream OpenAI error")

    return _to_plain(resp)


# --------------------------------------------------------------------------------------
# Generic HTTP forwarder for "batches" and other raw endpoints
# --------------------------------------------------------------------------------------


async def forward_openai_request(
    method: str,
    path: str,
    json_body: Optional[Dict[str, Any]] = None,
    params: Optional[Mapping[str, Any]] = None,
) -> httpx.Response:
    """
    Generic HTTP forwarder that matches the old forward_openai_request signature.

    Used by routes like /v1/batches which expect to forward literally to
    api.openai.com, preserving status code and headers.
    """
    base_url = getattr(settings, "OPENAI_BASE_URL", None) or "https://api.openai.com/v1"
    base = base_url.rstrip("/")

    # Allow callers to pass "batches", "/batches", "v1/batches", or "/v1/batches".
    clean_path = path.lstrip("/")
    if not clean_path.startswith("v1/"):
        clean_path = f"v1/{clean_path}"
    url = f"{base}/{clean_path[3:]}" if base.endswith("/v1") else f"{base}/{clean_path}"

    headers = {
        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    logger.debug(
        "Raw forwarding to OpenAI: %s %s json=%s params=%s",
        method,
        url,
        json_body,
        params,
    )

    async with httpx.AsyncClient(timeout=None) as client:
        resp = await client.request(
            method=method.upper(),
            url=url,
            headers=headers,
            json=json_body,
            params=params,
        )

    return resp


__all__ = [
    "get_async_openai_client",
    "forward_responses_create",
    "forward_embeddings_create",
    "forward_models_list",
    "forward_models_retrieve",
    "forward_openai_request",
]
