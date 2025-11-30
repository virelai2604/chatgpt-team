# app/routes/vector_stores.py

from __future__ import annotations

from fastapi import APIRouter, Request, Response

from app.api.forward_openai import forward_openai_request
from app.utils.logger import relay_log as logger

router = APIRouter(
    prefix="/v1",
    tags=["vector_stores"],
)


@router.get("/vector_stores")
async def list_vector_stores(request: Request) -> Response:
    logger.info("[vector_stores] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.post("/vector_stores")
async def create_vector_store(request: Request) -> Response:
    logger.info("[vector_stores] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.get("/vector_stores/{vs_id}")
async def retrieve_vector_store(vs_id: str, request: Request) -> Response:
    logger.info("[vector_stores] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)
