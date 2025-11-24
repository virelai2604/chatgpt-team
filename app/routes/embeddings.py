from __future__ import annotations

from fastapi import APIRouter, Request, Response

from app.api.forward_openai import forward_openai_request

router = APIRouter(
    prefix="/v1",
    tags=["embeddings"],
)


@router.post("/embeddings")
async def create_embedding(request: Request) -> Response:
    return await forward_openai_request(request)
