# app/routes/images.py

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Body

from app.api.forward_openai import forward_images_generate
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/v1",
    tags=["images"],
)


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
