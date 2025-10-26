# ==========================================================
# app/routes/vector_stores.py — BIFL v2.3.4-fp (finalized)
# ==========================================================
# OpenAI-compatible proxy for vector store operations.
# Supports creation, retrieval, update, deletion, and batch import.
# Async, streaming-safe, and integrated with db_logger.
# ==========================================================

from fastapi import APIRouter, Request
from app.api.forward import forward_openai
from app.utils.db_logger import log_event

router = APIRouter(prefix="/v1/vector_stores", tags=["Vector Stores"])

# ----------------------------------------------------------
# 📦  Create / List Vector Stores
# ----------------------------------------------------------
@router.api_route("", methods=["GET", "POST"])
async def vector_store_root(request: Request):
    """
    GET → list vector stores
    POST → create a new vector store
    """
    response = await forward_openai(request, "/v1/vector_stores")
    try:
        await log_event("/v1/vector_stores", response.status_code, "root request")
    except Exception:
        pass
    return response


# ----------------------------------------------------------
# 🔍  Retrieve or Update Specific Store
# ----------------------------------------------------------
@router.api_route("/{store_id}", methods=["GET", "PATCH", "DELETE"])
async def manage_vector_store(request: Request, store_id: str):
    """
    GET → retrieve store details
    PATCH → update metadata
    DELETE → remove store
    """
    endpoint = f"/v1/vector_stores/{store_id}"
    response = await forward_openai(request, endpoint)
    try:
        await log_event(endpoint, response.status_code, f"store {store_id}")
    except Exception:
        pass
    return response


# ----------------------------------------------------------
# 📤  Batch Import or File Attachments
# ----------------------------------------------------------
@router.api_route("/{store_id}/batches", methods=["GET", "POST"])
async def handle_vector_batches(request: Request, store_id: str):
    """
    Handles large file uploads or embeddings batch imports.
    Automatically streams NDJSON for progress tracking.
    """
    endpoint = f"/v1/vector_stores/{store_id}/batches"
    response = await forward_openai(request, endpoint)
    try:
        await log_event(endpoint, response.status_code, "batch request")
    except Exception:
        pass
    return response
