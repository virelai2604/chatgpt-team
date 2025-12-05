# app/api/forward_openai.py

from __future__ import annotations

from typing import Any, Dict

from app.core.http_client import get_async_openai_client
from app.utils.logger import get_logger

logger = get_logger(__name__)


def _to_plain(result: Any) -> Any:
    """
    Convert OpenAI SDK result objects into JSON-serializable dicts when possible.
    """
    # Newer SDKs use Pydantic v2: model_dump / model_dump_json
    if hasattr(result, "model_dump"):
        try:
            return result.model_dump()
        except TypeError:
            # Some objects may not support model_dump with no args
            pass

    if hasattr(result, "to_dict"):
        try:
            return result.to_dict()
        except TypeError:
            pass

    # Fall back to returning the object; FastAPI may know how to serialize it.
    return result


# -------------------------
# Responses API
# -------------------------


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


# -------------------------
# Embeddings API
# -------------------------


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


# -------------------------
# Images API
# -------------------------


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


# -------------------------
# Videos API
# -------------------------


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


# -------------------------
# Models API
# -------------------------


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
