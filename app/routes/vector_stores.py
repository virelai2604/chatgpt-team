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

# Environment variables
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def headers():
    """
    Build default authorization header.
    Falls back safely if the environment variable is missing.
    """
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is not set in the environment.")
    return {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }


@router.get("")
async def list_vector_stores():
    """
    List all vector stores from OpenAI API.
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.get(f"{OPENAI_API_BASE}/vector_stores", headers=headers())
            return JSONResponse(resp.json(), status_code=resp.status_code)
        except httpx.HTTPStatusError as e:
            return JSONResponse({"error": f"HTTP error: {str(e)}"}, status_code=e.response.status_code)
        except Exception as e:
            return JSONResponse({"error": f"Unexpected error: {str(e)}"}, status_code=500)


@router.post("")
async def create_store(request: Request):
    """
    Create a new vector store in OpenAI API.
    """
    try:
        body = await request.body()
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{OPENAI_API_BASE}/vector_stores",
                headers=headers(),
                content=body,
            )
        return JSONResponse(resp.json(), status_code=resp.status_code)
    except httpx.HTTPStatusError as e:
        return JSONResponse({"error": f"HTTP error: {str(e)}"}, status_code=e.response.status_code)
    except Exception as e:
        return JSONResponse({"error": f"Unexpected error: {str(e)}"}, status_code=500)


@router.get("/{store_id}")
async def get_store(store_id: str):
    """
    Retrieve details for a specific vector store by ID.
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(f"{OPENAI_API_BASE}/vector_stores/{store_id}", headers=headers())
    return JSONResponse(resp.json(), status_code=resp.status_code)


@router.delete("/{store_id}")
async def delete_store(store_id: str):
    """
    Delete a specific vector store by ID.
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.delete(f"{OPENAI_API_BASE}/vector_stores/{store_id}", headers=headers())
    return JSONResponse(resp.json(), status_code=resp.status_code)
