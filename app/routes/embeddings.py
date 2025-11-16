"""
embeddings.py — Handles /v1/embeddings route
─────────────────────────────────────────────
Creates text embeddings via OpenAI API.
"""

import os
import httpx
from fastapi import APIRouter, Request, Response
from app.utils.logger import relay_log as logger

router = APIRouter(prefix="/v1/embeddings", tags=["embeddings"])

OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


@router.post("")
async def create_embedding(request: Request):
    data = await request.json()
    model = data.get("model", "text-embedding-3-small")
    logger.info(f"[Embeddings] model={model}")

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        res = await client.post(
            f"{OPENAI_API_BASE.rstrip('/')}/embeddings",
            json=data,
            headers=headers,
        )
        return Response(
            content=res.content,
            status_code=res.status_code,
            headers={
                "content-type": res.headers.get("content-type", "application/json")
            },
        )
