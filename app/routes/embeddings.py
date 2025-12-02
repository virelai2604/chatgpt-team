# app/routes/embeddings.py

from __future__ import annotations

from fastapi import APIRouter, Request, Response

from app.api.forward_openai import forward_openai_request

router = APIRouter(
    prefix="/v1",
    tags=["embeddings"],
)


@router.post("/embeddings")
async def create_embedding(request: Request) -> Response:
    """
    POST /v1/embeddings

    Thin proxy to OpenAI Embeddings API.
    """
    return await forward_openai_request(request)
