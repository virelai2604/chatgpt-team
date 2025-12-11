# app/api/forward_openai.py

from __future__ import annotations

import logging
from typing import Any, Dict, Mapping, Optional

from openai import AsyncOpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Shared client helper
# ---------------------------------------------------------------------------


_client: Optional[AsyncOpenAI] = None


async def get_async_openai_client() -> AsyncOpenAI:
    """
    Lazily construct and cache a single AsyncOpenAI client for the relay.

    This uses the API key and base URL from settings so that all routes
    share the same configuration.
    """
    global _client
    if _client is None:
        logger.info("Initializing AsyncOpenAI client for relay")
        _client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL,
        )
    return _client


def _to_plain(result: Any) -> Any:
    """
    Convert OpenAI SDK models (Pydantic-based) into plain Python data structures
    that FastAPI/JSON can serialize without involving Pydantic again.

    This helper is intentionally conservative: it only special-cases the
    OpenAI types that implement `model_dump` / `model_dump_json` and otherwise
    returns values as-is.
    """
    # OpenAI Python 1.x models
    if hasattr(result, "model_dump"):
        # `model_dump()` returns dict / list of primitive types
        return result.model_dump()

    # Async streams / streaming managers are *not* meant to be serialized;
    # callers must handle them separately and never run them through this helper.
    return result


# ---------------------------------------------------------------------------
# Typed helpers for specific endpoints
# ---------------------------------------------------------------------------


async def forward_responses_create(payload: Dict[str, Any]) -> Any:
    """
    Forward a non-streaming Responses.create call via the AsyncOpenAI client.

    NOTE: This helper is *non-streaming only*. Callers MUST NOT pass
    `stream=True` here. Streaming should be handled in the route code
    (e.g. wrapping the SDK's stream in a StreamingResponse / SSE).
    """
    if payload.get("stream"):
        # This is a guard so we don't accidentally hand an AsyncStream back to
        # FastAPI's JSON response machinery (which caused 500s before).
        raise ValueError(
            "forward_responses_create() must not be used with stream=True; "
            "handle streaming in the route and use the SDK's streaming API "
            "directly there."
        )

    client = await get_async_openai_client()
    logger.debug("Forwarding /v1/responses payload: %s", payload)

    result = await client.responses.create(**payload)
    return _to_plain(result)


async def forward_embeddings_create(payload: Dict[str, Any]) -> Any:
    """
    Forward an embeddings.create call via the AsyncOpenAI client.

    We intentionally *do not* force `encoding_format="base64"` here so that
    the response shape matches the official OpenAI API and the tests'
    expectations: `embedding` is a `list[float]`.

    If the caller explicitly sets `encoding_format` in the payload, we honor it.
    """
    client = await get_async_openai_client()
    logger.debug("Forwarding /v1/embeddings payload: %s", payload)

    # Do NOT override encoding_format unless you have a specific reason.
    # The default is float vectors, which is what tests expect.
    result = await client.embeddings.create(**payload)
    return _to_plain(result)


# ---------------------------------------------------------------------------
# Generic HTTP-style forwarder (if you use it elsewhere in the app)
# ---------------------------------------------------------------------------


async def forward_openai_request(
    method: str,
    path: str,
    json: Optional[Mapping[str, Any]] = None,
    params: Optional[Mapping[str, Any]] = None,
) -> Any:
    """
    Low-level passthrough for miscellaneous OpenAI endpoints that don't
    have a dedicated helper yet.

    This uses the AsyncOpenAI client’s `client._client` (underlying httpx)
    to make arbitrary requests, but still returns plain Python data.
    """
    client = await get_async_openai_client()
    url = f"{settings.OPENAI_BASE_URL}{path}"

    logger.debug(
        "Forwarding generic OpenAI request: %s %s params=%s json=%s",
        method,
        url,
        params,
        json,
    )

    # Use the underlying httpx client for maximum flexibility.
    http_client = client._client  # type: ignore[attr-defined]

    response = await http_client.request(
        method=method,
        url=url,
        params=params,
        json=json,
        headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
    )
    response.raise_for_status()

    return response.json()
