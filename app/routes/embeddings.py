# app/routes/embeddings.py

from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.api.forward_openai import forward_embeddings_create

logger = logging.getLogger(__name__)

# IMPORTANT:
# The OpenAI REST API path is /v1/embeddings.
# We add prefix="/v1" so this router exposes /v1/embeddings.
router = APIRouter(
    prefix="/v1",
    tags=["embeddings"],
)


@router.post("/embeddings")
async def create_embeddings(request: Request) -> JSONResponse:
    """
    Proxy /v1/embeddings to the OpenAI Embeddings API via AsyncOpenAI.

    This endpoint forwards the incoming JSON payload to OpenAI and returns
    the upstream JSON response as-is.
    """
    logger.info("Incoming /v1/embeddings request")
    body: Dict[str, Any] = await request.json()

    result = await forward_embeddings_create(body)
    return JSONResponse(content=result)
