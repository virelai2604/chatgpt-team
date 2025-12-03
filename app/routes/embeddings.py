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
    logger.info("→ [embeddings] POST %s", request.url.path)
    return await forward_openai_request(request)


@router.api_route(
    "/embeddings/{path:path}",
    methods=["GET", "POST", "HEAD", "OPTIONS"],
)
async def embeddings_subpaths(path: str, request: Request) -> Response:
    """
    Forward any future /v1/embeddings/* subroutes.
    """
    logger.info("→ [embeddings/*] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)
