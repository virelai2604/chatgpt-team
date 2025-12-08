# app/routes/models.py

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Path, Request, Response

from app.api.forward_openai import forward_openai_request
from app.utils.logger import relay_log as logger

router = APIRouter(
    prefix="/v1",
    tags=["models"],
)


@router.get("/models")
async def list_models(request: Request) -> Response:
    """
    Proxy for the OpenAI Models list API.

      - GET https://api.openai.com/v1/models

    In tests this goes through `forward_openai_request`, so the httpx
    mock and `forward_spy` fixtures see the correct method & path.
    """
    logger.info("→ [models] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.get("/models/{model_id}")
async def retrieve_model(
    request: Request,
    model_id: str = Path(..., description="Model ID to retrieve"),
) -> Response:
    """
    Proxy for the OpenAI Models retrieve API.

      - GET https://api.openai.com/v1/models/{model_id}
    """
    logger.info("→ [models] %s %s (id=%s)", request.method, request.url.path, model_id)
    return await forward_openai_request(request)


@router.delete("/models/{model_id}")
async def delete_model(
    request: Request,
    model_id: str = Path(..., description="Model ID to delete"),
) -> Response:
    """
    Proxy for the OpenAI Models delete API.

      - DELETE https://api.openai.com/v1/models/{model_id}

    Tests:
      - `test_models_delete_error_passthrough`
      - `test_delete_model_forward`

    These expect:
      * The request is forwarded as DELETE /v1/models/{model_id}
      * Upstream 4xx errors (e.g. 404) are passed through unchanged.
    """
    logger.info("→ [models] %s %s (id=%s)", request.method, request.url.path, model_id)
    return await forward_openai_request(request)
