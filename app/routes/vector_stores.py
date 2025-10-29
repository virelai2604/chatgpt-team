# ==========================================================
# app/routes/vector_stores.py — Ground Truth OpenAI-Compatible Mirror
# ==========================================================
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from app.api.forward_openai import forward_openai_request

router = APIRouter(prefix="/v1/vector_stores", tags=["Vector Stores"])

@router.api_route("", methods=["GET", "POST"])
async def vector_store_root(request: Request):
    """
    GET  → List vector stores
    POST → Create a new vector store
    Mirrors OpenAI /v1/vector_stores
    """
    body = await request.json() if request.method == "POST" else None
    result = await forward_openai_request("v1/vector_stores", method=request.method, json_data=body)
    return JSONResponse(result)

@router.api_route("/{store_id}", methods=["GET", "PATCH", "DELETE"])
async def manage_vector_store(request: Request, store_id: str):
    """
    GET    → Retrieve vector store metadata
    PATCH  → Update vector store attributes
    DELETE → Remove vector store
    Mirrors OpenAI /v1/vector_stores/{store_id}
    """
    body = await request.json() if request.method == "PATCH" else None
    endpoint = f"v1/vector_stores/{store_id}"
    result = await forward_openai_request(endpoint, method=request.method, json_data=body)
    return JSONResponse(result)

@router.api_route("/{store_id}/batches", methods=["GET", "POST"])
async def handle_vector_batches(request: Request, store_id: str):
    """
    GET  → List embedding import batches
    POST → Create/import new batch of vectors
    Mirrors OpenAI /v1/vector_stores/{store_id}/batches
    """
    body = await request.json() if request.method == "POST" else None
    endpoint = f"v1/vector_stores/{store_id}/batches"
    result = await forward_openai_request(endpoint, method=request.method, json_data=body)
    return JSONResponse(result)
