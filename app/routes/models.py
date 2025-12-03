# app/routes/models.py

from __future__ import annotations

from fastapi import APIRouter, Request, Response

from app.api.forward_openai import forward_openai_request
from app.utils.logger import relay_log as logger

router = APIRouter(
    prefix="/v1",
    tags=["models"],
)


@router.get("/models")
async def list_models(request: Request) -> Response:
    logger.info("→ [models] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.get("/models/{model_id}")
async def retrieve_model(model_id: str, request: Request) -> Response:
    logger.info("→ [models] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.delete("/models/{model_id}")
async def delete_model(model_id: str, request: Request) -> Response:
    """
    DELETE /v1/models/{model_id} — delete fine-tuned model (OpenAI parity).
    """
    logger.info("→ [models] DELETE %s", request.url.path)
    return await forward_openai_request(request)
