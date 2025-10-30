# ==========================================================
# app/routes/vector_stores.py — Vector Store Management
# ==========================================================
"""
Handles /v1/vector_stores endpoints for list, create, update, and delete.
Ground Truth Edition ensures parity with OpenAI’s RAG APIs.
"""

from fastapi import APIRouter, Request
from app.api.forward_openai import forward_openai_request

router = APIRouter(prefix="/v1/vector_stores", tags=["Vector Stores"])


@router.get("")
async def list_vector_stores():
    """List vector stores."""
    return await forward_openai_request("v1/vector_stores", method="GET")


@router.post("")
async def create_vector_store(request: Request):
    """Create a new vector store."""
    body = await request.json()
    return await forward_openai_request("v1/vector_stores", method="POST", json=body)


@router.get("/{store_id}")
async def get_vector_store(store_id: str):
    """Get details of a specific vector store."""
    return await forward_openai_request(f"v1/vector_stores/{store_id}", method="GET")


@router.patch("/{store_id}")
async def update_vector_store(store_id: str, request: Request):
    """Update an existing vector store."""
    body = await request.json()
    return await forward_openai_request(f"v1/vector_stores/{store_id}", method="PATCH", json=body)


@router.delete("/{store_id}")
async def delete_vector_store(store_id: str):
    """Delete a vector store."""
    return await forward_openai_request(f"v1/vector_stores/{store_id}", method="DELETE")
