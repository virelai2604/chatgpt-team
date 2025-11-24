from __future__ import annotations

from fastapi import APIRouter, Request, Response

from app.api.forward_openai import forward_openai_request

router = APIRouter(tags=["vector_stores"])


@router.get("/v1/vector_stores")
async def list_vector_stores(request: Request) -> Response:
    return await forward_openai_request(request)


@router.post("/v1/vector_stores")
async def create_vector_store(request: Request) -> Response:
    return await forward_openai_request(request)


@router.get("/v1/vector_stores/{vs_id}")
async def retrieve_vector_store(vs_id: str, request: Request) -> Response:
    return await forward_openai_request(request)
