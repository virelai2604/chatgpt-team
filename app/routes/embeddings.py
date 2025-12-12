# app/routes/embeddings.py

from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.api.forward_openai import forward_embeddings_create

logger = logging.getLogger(__name__)

# FIX: mount under /v1 so tests calling /v1/embeddings resolve correctly
router = APIRouter(prefix="/v1", tags=["embeddings"])


@router.post("/embeddings")
async def create_embeddings(request: Request) -> JSONResponse:
    """
    Proxy /v1/embeddings to the OpenAI Embeddings API via AsyncOpenAI.

    We return raw JSON so tests can assert:
      - body["object"] == "list"
      - body["data"][0]["embedding"] is list[float]
    """
    logger.info("Incoming /v1/embeddings request")
    body: Dict[str, Any] = await request.json()

    result = await forward_embeddings_create(body)
    return JSONResponse(content=result)
