# ==========================================================
# app/routes/vector_stores.py — Relay v2025-10 Ground Truth Mirror
# ==========================================================
# Fully OpenAI-compatible /v1/vector_stores endpoint.
# Supports creation, retrieval, updates, deletion,
# and batch embedding imports.
# ==========================================================

from fastapi import APIRouter, Request
from app.api.forward_openai import forward_openai
from app.utils.db_logger import setup_logging, logging

router = APIRouter(prefix="/v1/vector_stores", tags=["Vector Stores"])

# ----------------------------------------------------------
# 📦  Create / List Vector Stores
# ----------------------------------------------------------
@router.api_route("", methods=["GET", "POST"])
async def vector_store_root(request: Request):
    """
    GET → list vector stores
    POST → create a new vector store
    Mirrors OpenAI /v1/vector_stores
    """
    response = await forward_openai(request, "/v1/vector_stores")
    try:
        await log_event("/v1/vector_stores", response.status_code, "root request")
    except Exception:
        pass
    return response


# ----------------------------------------------------------
# 🔍  Retrieve / Update / Delete Specific Store
# ----------------------------------------------------------
@router.api_route("/{store_id}", methods=["GET", "PATCH", "DELETE"])
async def manage_vector_store(request: Request, store_id: str):
    """
    GET → retrieve store details
    PATCH → update metadata
    DELETE → remove store
    Mirrors OpenAI /v1/vector_stores/{store_id}
    """
    endpoint = f"/v1/vector_stores/{store_id}"
    response = await forward_openai(request, endpoint)
    try:
        await log_event(endpoint, response.status_code, f"store {store_id}")
    except Exception:
        pass
    return response


# ----------------------------------------------------------
# 📤  Batch Import or Attachments
# ----------------------------------------------------------
@router.api_route("/{store_id}/batches", methods=["GET", "POST"])
async def handle_vector_batches(request: Request, store_id: str):
    """
    Handles large embedding imports or NDJSON-based
    batch uploads. Mirrors OpenAI /v1/vector_stores/{id}/batches
    """
    endpoint = f"/v1/vector_stores/{store_id}/batches"
    response = await forward_openai(request, endpoint)
    try:
        await log_event(endpoint, response.status_code, "batch request")
    except Exception:
        pass
    return response
