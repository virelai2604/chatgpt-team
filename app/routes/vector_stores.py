"""
vector_stores.py — /v1/vector_stores
────────────────────────────────────
Implements all CRUD operations for vector stores.
"""

import os
import httpx
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/v1/vector_stores", tags=["vector_stores"])

OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def headers():
    return {"Authorization": f"Bearer {OPENAI_API_KEY}"}

@router.post("")
async def create_store(request: Request):
    body = await request.body()
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{OPENAI_API_BASE}/vector_stores", headers=headers(), content=body)
    return JSONResponse(resp.json(), status_code=resp.status_code)
