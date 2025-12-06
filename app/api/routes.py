# app/api/routes.py

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Body, HTTPException, Path, status

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

router = APIRouter(prefix="/v1", tags=["openai-sdk"])


@router.post(
    "/responses",
    summary="Create a model response (Responses API)",
)
async def create_response(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    try:
        return await forward_responses_create(payload)
    except Exception as exc:  # pragma: no cover
        logger.exception("Error calling Responses API: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Error calling OpenAI Responses API",
        )


@router.post(
    "/embeddings",
    summary="Create embeddings",
)
async def create_embeddings(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    try:
        return await forward_embeddings_create(payload)
    except Exception as exc:  # pragma: no cover
        logger.exception("Error calling Embeddings API: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Error calling OpenAI Embeddings API",
        )


@router.post(
    "/images",
    summary="Generate images",
)
async def generate_images(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    try:
        return await forward_images_generate(payload)
    except Exception as exc:  # pragma: no cover
        logger.exception("Error calling Images API: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Error calling OpenAI Images API",
        )


@router.post(
    "/videos",
    summary="Generate videos",
)
async def create_videos(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    try:
        return await forward_videos_create(payload)
    except Exception as exc:  # pragma: no cover
        logger.exception("Error calling Videos API: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Error calling OpenAI Videos API",
        )


@router.get(
    "/models",
    summary="List available models",
)
async def list_models() -> Dict[str, Any]:
    try:
        return await forward_models_list()
    except Exception as exc:  # pragma: no cover
        logger.exception("Error listing models: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Error listing OpenAI models",
        )


@router.get(
    "/models/{model_id}",
    summary="Retrieve model metadata",
)
async def retrieve_model(
    model_id: str = Path(..., description="Model ID to retrieve"),
) -> Dict[str, Any]:
    try:
        return await forward_models_retrieve(model_id)
    except Exception as exc:  # pragma: no cover
        logger.exception("Error retrieving model %s: %s", model_id, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Error retrieving OpenAI model {model_id}",
        )
