# app/routes/videos.py

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Body

from app.api.forward_openai import forward_videos_create
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/v1",
    tags=["videos"],
)


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
