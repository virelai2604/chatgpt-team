from __future__ import annotations

from fastapi import APIRouter, Request, Response

from app.api.forward_openai import forward_openai_request

router = APIRouter(tags=["models"])


@router.get("/v1/models")
async def list_models(request: Request) -> Response:
    """
    GET /v1/models
    """
    return await forward_openai_request(request)


@router.get("/v1/models/{model_id}")
async def retrieve_model(model_id: str, request: Request) -> Response:
    """
    GET /v1/models/{model_id}
    """
    return await forward_openai_request(request)
