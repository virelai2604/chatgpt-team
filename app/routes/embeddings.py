from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, Response as FastAPIResponse
from openai.types.create_embedding_response import CreateEmbeddingResponse
from starlette.requests import ClientDisconnect

from app.api.forward_openai import forward_embeddings_create
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/v1/embeddings")
async def create_embeddings(request: Request) -> Any:
    logger.info("Incoming /v1/embeddings request")

    try:
        body: Dict[str, Any] = await request.json()
    except ClientDisconnect:
        return FastAPIResponse(status_code=499)

    resp: CreateEmbeddingResponse = await forward_embeddings_create(body)
    return JSONResponse(content=resp.model_dump())
