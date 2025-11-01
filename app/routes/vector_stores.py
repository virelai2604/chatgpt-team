# ================================================================
# vector_stores.py — Vector Store CRUD Routes
# ================================================================
# Fully implements mock CRUD operations for /v1/vector_stores
# Endpoints covered by tests:
#   POST /v1/vector_stores        → create
#   GET  /v1/vector_stores/{id}   → retrieve
#   DELETE /v1/vector_stores/{id} → delete
# ================================================================

from fastapi import APIRouter
from fastapi.responses import JSONResponse
import time, uuid

router = APIRouter(prefix="/v1/vector_stores", tags=["vector_stores"])

# In-memory vector store registry
VECTOR_STORES = {}

@router.post("")
async def create_vector_store():
    """
    Create a mock vector store.
    """
    vs_id = f"vs_{uuid.uuid4().hex[:8]}"
    vs_data = {
        "object": "vector_store",
        "id": vs_id,
        "created_at": int(time.time()),
        "status": "ready",
        "metadata": {"scope": "unit"}
    }
    VECTOR_STORES[vs_id] = vs_data
    return JSONResponse(vs_data)

@router.get("/{vs_id}")
async def get_vector_store(vs_id: str):
    """
    Retrieve a vector store by ID.
    """
    vs = VECTOR_STORES.get(vs_id)
    if not vs:
        return JSONResponse({
            "error": {"message": "Vector store not found", "type": "not_found"}
        }, status_code=404)
    return JSONResponse(vs)

@router.delete("/{vs_id}")
async def delete_vector_store(vs_id: str):
    """
    Delete a vector store by ID.
    """
    if vs_id in VECTOR_STORES:
        del VECTOR_STORES[vs_id]
        return JSONResponse({
            "object": "vector_store.deleted",
            "id": vs_id,
            "deleted": True
        })
    return JSONResponse({
        "error": {"message": "Vector store not found", "type": "not_found"}
    }, status_code=404)
