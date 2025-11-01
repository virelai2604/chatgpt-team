# ==========================================================
# app/routes/vector_stores.py — Ground Truth Edition (rev.2025.11)
# ==========================================================
"""
Implements the OpenAI-compatible /v1/vector_stores endpoints.

Behavior:
  ✅ POST   /v1/vector_stores           — create a new vector store
  ✅ GET    /v1/vector_stores           — list all vector stores
  ✅ GET    /v1/vector_stores/{id}      — retrieve a specific store
  ✅ DELETE /v1/vector_stores/{id}      — delete a store
  🚫 PATCH/PUT                         — 405 (not supported)

Used by:
  • /v1/responses (CHAIN_WAIT_MODE) for vector chaining
  • SDK parity tests via openai-python client
"""

import uuid
from datetime import datetime
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse

try:
    from app.api.forward_openai import forward_openai_request
except ImportError:
    forward_openai_request = None

router = APIRouter(prefix="/v1/vector_stores", tags=["Vector Stores"])

# ---------------------------------------------------------------------
# Global in-memory registry (importable by responses.py)
# ---------------------------------------------------------------------
VECTOR_STORE_REGISTRY = {}  # ← this is what responses.py imports


# ---------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------
@router.post("")
async def create_vector_store(request: Request):
    """Create a new vector store (mock or passthrough)."""
    try:
        payload = await request.json()
    except Exception:
        payload = {}

    vs_id = f"vs_{uuid.uuid4().hex[:8]}"
    store = {
        "id": vs_id,
        "object": "vector_store",
        "created_at": int(datetime.now().timestamp()),
        "name": payload.get("name", "default-store"),
        "status": "ready",
        "vectors": [],
    }
    VECTOR_STORE_REGISTRY[vs_id] = store
    return JSONResponse(content=store, status_code=200)


# ---------------------------------------------------------------------
# List
# ---------------------------------------------------------------------
@router.get("")
async def list_vector_stores():
    """List all vector stores."""
    return JSONResponse(
        content={"object": "list", "data": list(VECTOR_STORE_REGISTRY.values())},
        status_code=200,
    )


# ---------------------------------------------------------------------
# Retrieve
# ---------------------------------------------------------------------
@router.get("/{store_id}")
async def retrieve_vector_store(store_id: str):
    """Retrieve a single vector store by ID."""
    store = VECTOR_STORE_REGISTRY.get(store_id)
    if not store:
        raise HTTPException(status_code=404, detail="Vector store not found")
    return JSONResponse(content=store, status_code=200)


# ---------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------
@router.delete("/{store_id}")
async def delete_vector_store(store_id: str):
    """Delete a vector store."""
    if store_id not in VECTOR_STORE_REGISTRY:
        raise HTTPException(status_code=404, detail="Vector store not found")
    del VECTOR_STORE_REGISTRY[store_id]
    return JSONResponse(content={"deleted": True, "id": store_id}, status_code=200)


# ---------------------------------------------------------------------
# Unsupported Methods
# ---------------------------------------------------------------------
@router.api_route("/{path:path}", methods=["PATCH", "PUT"])
async def unsupported_methods(path: str):
    """Return 405 for unsupported update methods."""
    raise HTTPException(status_code=405, detail="Method Not Allowed (PATCH/PUT not supported)")


# ---------------------------------------------------------------------
# Optional: Forward to upstream OpenAI if configured
# ---------------------------------------------------------------------
@router.api_route("/{path:path}", methods=["POST", "GET", "DELETE"], include_in_schema=False)
async def forward_if_configured(request: Request, path: str):
    """Forward requests to the real OpenAI API if enabled."""
    if not forward_openai_request:
        raise HTTPException(status_code=501, detail="Upstream forwarding not configured")

    method = request.method
    body = None
    try:
        if "application/json" in request.headers.get("content-type", ""):
            body = await request.json()
    except Exception:
        body = None

    result = await forward_openai_request(
        path=f"/v1/vector_stores/{path}",
        body=body,
        stream=False,
        request=request,
    )
    return result
