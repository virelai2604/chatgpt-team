# app/routes/vector_stores.py

from fastapi import APIRouter, Request, Response

from app.api.forward_openai import forward_openai_request

router = APIRouter(
    prefix="/vector_stores",
    tags=["vector_stores"],
)


@router.api_route(
    "",
    methods=["GET", "POST"],
)
@router.api_route(
    "/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
)
async def proxy_vector_stores(request: Request, path: str = "") -> Response:
    """
    Catch-all proxy for OpenAI Vector Stores endpoints.

    Examples:
      - GET  /v1/vector_stores
      - POST /v1/vector_stores
      - GET  /v1/vector_stores/{id}
      - POST /v1/vector_stores/{id}/file_batches
      - etc.

    All logic is delegated to `forward_openai_request`.
    """
    return await forward_openai_request(request)
