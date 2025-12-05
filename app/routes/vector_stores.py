# app/routes/vector_stores.py

from __future__ import annotations

from fastapi import APIRouter, Request, Response

from app.api.forward_openai import forward_openai_request
from app.utils.logger import relay_log as logger  # type: ignore[attr-defined]

router = APIRouter(
    prefix="/v1",
    tags=["vector_stores"],
)


@router.api_route("/vector_stores", methods=["GET", "POST", "HEAD", "OPTIONS"])
async def vector_stores_root(request: Request) -> Response:
    """
    Root for the Vector Stores API.

    Typical operations:

      - GET  /v1/vector_stores   → list vector stores
      - POST /v1/vector_stores   → create vector store
    """
    logger.info("→ [vector_stores] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.api_route(
    "/vector_stores/{path:path}",
    methods=["GET", "POST", "DELETE", "PATCH", "HEAD", "OPTIONS"],
)
async def vector_stores_subpaths(path: str, request: Request) -> Response:
    """
    Catch‑all for /v1/vector_stores/*.

    Examples, consistent with OpenAI Vector Stores API:

      - GET    /v1/vector_stores/{vector_store_id}
      - DELETE /v1/vector_stores/{vector_store_id}
      - GET    /v1/vector_stores/{vector_store_id}/files
      - POST   /v1/vector_stores/{vector_store_id}/files
      - GET    /v1/vector_stores/{vector_store_id}/file_batches
      - POST   /v1/vector_stores/{vector_store_id}/file_batches
      - etc.
    """
    logger.info("→ [vector_stores/*] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)
