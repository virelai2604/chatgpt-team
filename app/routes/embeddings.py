# app/routes/embeddings.py

from __future__ import annotations

from fastapi import APIRouter, Request, Response

from app.api.forward_openai import forward_openai_request
from app.utils.logger import relay_log as logger

router = APIRouter(
    prefix="/v1",
    tags=["embeddings"],
)


@router.post("/embeddings")
async def create_embedding(request: Request) -> Response:
    """
    POST /v1/embeddings — standard embeddings creation endpoint.
    """
    logger.info("→ [embeddings] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)
