from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, Response as FastAPIResponse
from starlette.requests import ClientDisconnect

from app.api.forward_openai import forward_embeddings_create
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/v1/embeddings")
async def create_embeddings(request: Request) -> Any:
    try:
        body: Dict[str, Any] = await request.json()
    except ClientDisconnect:
        return FastAPIResponse(status_code=499)

    logger.info("Incoming /v1/embeddings request")
    resp = await forward_embeddings_create(body)

    # Note: OpenAI may return base64 embeddings when encoding_format=base64;
    # the SDK may warn during serialization, but the payload is still valid.
    return JSONResponse(content=resp.model_dump())
