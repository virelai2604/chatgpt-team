# app/routes/vector_stores.py

from __future__ import annotations

from fastapi import APIRouter, Request, Response

from app.api.forward_openai import forward_openai_request
from app.utils.logger import relay_log as logger

router = APIRouter(
    prefix="/v1",
    tags=["vector_stores"],
)


@router.api_route("/vector_stores", methods=["GET", "POST", "HEAD", "OPTIONS"])
async def vector_stores_root(request: Request) -> Response:
    """
    Root for Vector Stores.

    Examples:
      - GET  /v1/vector_stores   (list stores)
      - POST /v1/vector_stores   (create store)
    """
    logger.info("→ [vector_stores] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.api_route(
    "/vector_stores/{path:path}",
    methods=["GET", "POST", "DELETE", "HEAD", "OPTIONS"],
)
async def vector_stores_subpaths(path: str, request: Request) -> Response:
    """
    Catch‑all for /v1/vector_stores/* subresources.

    Examples:
      - /v1/vector_stores/{store_id}
      - /v1/vector_stores/{store_id}/files
      - /v1/vector_stores/{store_id}/files/{file_id}
    """
    logger.info("→ [vector_stores/*] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)
