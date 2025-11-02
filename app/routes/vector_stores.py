# ================================================================
# vector_stores.py — CRUD passthrough for /v1/vector_stores
# ================================================================
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from app.api.forward_openai import forward_to_openai

router = APIRouter(prefix="/v1/vector_stores", tags=["vector_stores"])

@router.post("")
async def create_vector_store(request: Request):
    resp = await forward_to_openai(request, "/v1/vector_stores")
    return JSONResponse(resp.json(), status_code=resp.status_code)

@router.get("/{vector_id}")
async def retrieve_vector_store(vector_id: str, request: Request):
    resp = await forward_to_openai(request, f"/v1/vector_stores/{vector_id}")
    return JSONResponse(resp.json(), status_code=resp.status_code)

@router.delete("/{vector_id}")
async def delete_vector_store(vector_id: str, request: Request):
    resp = await forward_to_openai(request, f"/v1/vector_stores/{vector_id}")
    return JSONResponse(resp.json(), status_code=resp.status_code)
