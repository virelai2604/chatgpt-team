# app/routes/embeddings.py

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Body

from app.api.forward_openai import forward_embeddings_create
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/v1",
    tags=["embeddings"],
)


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
