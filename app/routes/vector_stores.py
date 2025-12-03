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
async def proxy_vector_stores_root(request: Request) -> Response:
    """
    Vector stores root.

    Covers:
      - GET  /v1/vector_stores   (list stores)
      - POST /v1/vector_stores   (create store)
    """
    logger.info("→ [vector_stores] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.api_route(
    "/vector_stores/{path:path}",
    methods=["GET", "POST", "DELETE", "PATCH", "HEAD", "OPTIONS"],
)
async def proxy_vector_stores_subpaths(path: str, request: Request) -> Response:
    """
    Catch-all for vector store subresources.

    Examples:
      - GET    /v1/vector_stores/{vector_store_id}
      - POST   /v1/vector_stores/{vector_store_id}                 (update)
      - DELETE /v1/vector_stores/{vector_store_id}                 (delete)
      - POST   /v1/vector_stores/{vector_store_id}/files           (attach file)
      - GET    /v1/vector_stores/{vector_store_id}/files           (list files)
      - GET    /v1/vector_stores/{vector_store_id}/files/{file_id}
      - DELETE /v1/vector_stores/{vector_store_id}/files/{file_id}
      - POST   /v1/vector_stores/{vector_store_id}/file_batches
      - GET    /v1/vector_stores/{vector_store_id}/file_batches/{batch_id}
      - any future /v1/vector_stores/* additions
    """
    logger.info("→ [vector_stores/*] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)
