# ==========================================================
# vector_stores.py — /v1/vector_stores
# ==========================================================
import httpx
from fastapi import APIRouter, Request
from app.api.forward_openai import forward_openai_request

router = APIRouter(prefix="/v1/vector_stores", tags=["Vector Stores"])


@router.get("")
async def list_vector_stores():
    return await forward_openai_request("v1/vector_stores", method="GET")


@router.post("")
async def create_vector_store(request: Request):
    try:
        body = await request.json()
    except Exception:
        body = {}
    return await forward_openai_request("v1/vector_stores", method="POST", json_data=body)


@router.get("/{store_id}")
async def get_vector_store(store_id: str):
    return await forward_openai_request(f"v1/vector_stores/{store_id}", method="GET")


@router.patch("/{store_id}")
async def update_vector_store(store_id: str, request: Request):
    body = await request.json()
    # Coerce metadata values to strings (OpenAI requires string values)
    if "metadata" in body and isinstance(body["metadata"], dict):
        body["metadata"] = {k: str(v) for k, v in body["metadata"].items()}

    try:
        return await forward_openai_request(f"v1/vector_stores/{store_id}", method="PATCH", json_data=body)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 405:
            # Fallback to POST if PATCH unsupported
            return await forward_openai_request(f"v1/vector_stores/{store_id}", method="POST", json_data=body)
        raise


@router.delete("/{store_id}")
async def delete_vector_store(store_id: str):
    return await forward_openai_request(f"v1/vector_stores/{store_id}", method="DELETE")
