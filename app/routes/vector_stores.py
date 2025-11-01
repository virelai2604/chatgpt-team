"""
vector_stores.py — /v1/vector_stores
CRUD for vector store metadata. Retrieval handled by tool.
"""

from fastapi import APIRouter, Request, HTTPException
import uuid
import time

router = APIRouter()
VECTOR_STORES = {}

@router.post("/v1/vector_stores")
async def create_vector_store(request: Request):
    body = await request.json()
    vs_id = f"vs_{uuid.uuid4().hex[:10]}"
    VECTOR_STORES[vs_id] = {
        "id": vs_id,
        "object": "vector_store",
        "created": int(time.time()),
        "metadata": body.get("metadata", {}),
    }
    return VECTOR_STORES[vs_id]

@router.get("/v1/vector_stores")
async def list_vector_stores():
    return {"object": "list", "data": list(VECTOR_STORES.values())}

@router.get("/v1/vector_stores/{id}")
async def get_vector_store(id: str):
    vs = VECTOR_STORES.get(id)
    if not vs:
        raise HTTPException(status_code=404, detail="Vector store not found")
    return vs

@router.delete("/v1/vector_stores/{id}")
async def delete_vector_store(id: str):
    if id in VECTOR_STORES:
        del VECTOR_STORES[id]
    return {"id": id, "object": "vector_store", "deleted": True}
