# app/routes/models.py

from fastapi import APIRouter, Request, Response

from app.api.forward_openai import forward_openai_request

router = APIRouter(
    prefix="/models",
    tags=["models"],
)


@router.api_route(
    "",
    methods=["GET"],
)
@router.api_route(
    "/{path:path}",
    methods=["GET"],
)
async def proxy_models(request: Request, path: str = "") -> Response:
    """
    Catch-all proxy for OpenAI Models API.

    Normal cases:
      - GET /v1/models           -> list models
      - GET /v1/models/{model}   -> retrieve model
    """
    return await forward_openai_request(request)
