"""
embeddings.py — /v1/embeddings
───────────────────────────────
Forwards embedding generation to OpenAI API.
"""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from app.api.forward_openai import forward_to_openai

router = APIRouter(prefix="/v1/embeddings", tags=["embeddings"])

@router.post("")
async def create_embedding(request: Request):
    return await forward_to_openai(request, "/v1/embeddings")

@router.get("")
async def get_embedding_status():
    return JSONResponse(
        {"error": "GET /v1/embeddings not supported. Use POST instead."},
        status_code=404,
    )
