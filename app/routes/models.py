# app/routes/models.py

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Path

from app.api.forward_openai import forward_models_list, forward_models_retrieve
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/v1",
    tags=["models"],
)


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
