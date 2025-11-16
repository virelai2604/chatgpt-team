"""
vector_stores.py — /v1/vector_stores
────────────────────────────────────
Handles vector store lifecycle and basic creation/list operations.
"""

import os
import httpx
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.utils.logger import relay_log as log

router = APIRouter(prefix="/v1/vector_stores", tags=["vector_stores"])

OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


def auth_headers():
    return {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }


@router.get("")
async def list_vector_stores():
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.get(
            f"{OPENAI_API_BASE.rstrip('/')}/vector_stores",
            headers=auth_headers(),
        )
        return JSONResponse(resp.json(), status_code=resp.status_code)


@router.post("")
async def create_vector_store(request: Request):
    body = await request.json()
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            f"{OPENAI_API_BASE.rstrip('/')}/vector_stores",
            headers=auth_headers(),
            json=body,
        )
        return JSONResponse(resp.json(), status_code=resp.status_code)
