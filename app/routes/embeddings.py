# app/routes/embeddings.py

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Body

from app.api.forward_openai import forward_embeddings_create
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/v1", tags=["openai-relay"])


@router.post("/embeddings")
async def create_embeddings(
    body: Dict[str, Any] = Body(
        ...,
        description="OpenAI Embeddings.create payload",
    ),
) -> Dict[str, Any]:
    """
    Relay endpoint for /v1/embeddings.

    This forwards the request body to OpenAI's embeddings.create using the
    official AsyncOpenAI SDK and returns the plain JSON result.

    The response shape matches the OpenAI API:

      {
        "object": "list",
        "data": [
          {
            "object": "embedding",
            "index": 0,
            "embedding": [float, float, ...]
          },
          ...
        ],
        ...
      }

    which is exactly what the integration test asserts against.
    """
    logger.info("Incoming /v1/embeddings request")
    logger.debug("Embeddings request body: %s", body)

    result = await forward_embeddings_create(body)

    # `forward_embeddings_create` already returns plain data (dict/list), so we
    # can return it directly and let FastAPI/Starlette JSON encode it.
    return result  # type: ignore[return-value]
