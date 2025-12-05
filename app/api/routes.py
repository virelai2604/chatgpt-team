# app/api/routes.py

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Body, Path

from app.api.forward_openai import (
    forward_embeddings_create,
    forward_images_generate,
    forward_models_list,
    forward_models_retrieve,
    forward_responses_create,
    forward_videos_create,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/v1", tags=["openai-relay"])


@router.post("/responses")
async def create_response(
    body: Dict[str, Any] = Body(..., description="OpenAI Responses.create payload"),
) -> Any:
    """
    Proxy for OpenAI Responses API.

    Expects the same JSON body that you would send directly to:
        POST https://api.openai.com/v1/responses
    """
    logger.info("Incoming /v1/responses request")
    return await forward_responses_create(body)


@router.post("/embeddings")
async def create_embedding(
    body: Dict[str, Any] = Body(..., description="OpenAI Embeddings.create payload"),
) -> Any:
    """
    Proxy for OpenAI Embeddings API.

    Expects the same JSON body that you would send directly to:
        POST https://api.openai.com/v1/embeddings
    """
    logger.info("Incoming /v1/embeddings request")
    return await forward_embeddings_create(body)


@router.post("/images")
@router.post("/images/generations")
async def generate_image(
    body: Dict[str, Any] = Body(..., description="OpenAI Images.generate payload"),
) -> Any:
    """
    Proxy for OpenAI Images API.

    Supports both /v1/images and /v1/images/generations path shapes to play
    nicely with different client assumptions.
    """
    logger.info("Incoming /v1/images request")
    return await forward_images_generate(body)


@router.post("/videos")
async def create_video(
    body: Dict[str, Any] = Body(..., description="OpenAI Videos.create payload"),
) -> Any:
    """
    Proxy for OpenAI Videos API.

    Expects the same JSON body you would send directly to:
        POST https://api.openai.com/v1/videos
    """
    logger.info("Incoming /v1/videos request")
    return await forward_videos_create(body)


@router.get("/models")
async def list_models() -> Any:
    """
    Proxy for OpenAI Models API (list).

    Equivalent to:
        GET https://api.openai.com/v1/models
    """
    logger.info("Incoming /v1/models list request")
    return await forward_models_list()


@router.get("/models/{model_id}")
async def retrieve_model(
    model_id: str = Path(..., description="Model ID to retrieve"),
) -> Any:
    """
    Proxy for OpenAI Models API (retrieve a specific model).
    """
    logger.info("Incoming /v1/models/%s retrieve request", model_id)
    return await forward_models_retrieve(model_id)
