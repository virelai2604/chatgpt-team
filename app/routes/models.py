# app/routes/models.py

from __future__ import annotations

from fastapi import APIRouter, Request, Response

from app.api.forward_openai import forward_openai_request

router = APIRouter(
    prefix="/v1",
    tags=["models"],
)


@router.get("/models")
async def list_models(request: Request) -> Response:
    """
    GET /v1/models

    List available models from OpenAI.
    """
    return await forward_openai_request(request)


@router.get("/models/{model_id}")
async def retrieve_model(model_id: str, request: Request) -> Response:
    """
    GET /v1/models/{model_id}

    Retrieve metadata for a specific model.
    """
    return await forward_openai_request(request)
