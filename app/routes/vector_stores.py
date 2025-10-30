# ==========================================================
# app/routes/vector_stores.py — Ground Truth Edition (rev.2025.10)
# ==========================================================
"""
Implements the OpenAI-compatible /v1/vector_stores endpoints.

This route mirrors the current OpenAI Vector Stores API behavior:

  ✅ POST   /v1/vector_stores           — create a new vector store
  ✅ GET    /v1/vector_stores           — list all vector stores
  ✅ GET    /v1/vector_stores/{id}      — retrieve a specific vector store
  ✅ DELETE /v1/vector_stores/{id}      — delete a vector store
  🚫 PATCH  /v1/vector_stores/{id}      — not supported (returns 405)
  🚫 PUT    /v1/vector_stores/{id}      — not supported (returns 405)

If OPENAI_API_KEY is configured, this module can be extended to forward
real upstream requests via forward_openai_request(); otherwise it runs in
local mock mode with an in-memory registry.
"""

import uuid
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse

# Optional: forwarder if you want to connect live to OpenAI
try:
    from app.api.forward_openai import forward_openai_request
except ImportError:
    forward_openai_request = None

router = APIRouter(prefix="/v1/vector_stores", tags=["Vector Stores"])

# ---------------------------------------------------------------------
# Local in-memory registry for mock mode
# ---------------------------------------------------------------------
VECTOR_STORES = {}

# ---------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------
@router.post("")
async def create_vector_store(request: Request):
    """
    Create a new vector store.

    Expected body: {"name": "my_store"}
    Returns a vector store object.
    """
    try:
        payload = await request.json()
    except Exception:
        payload = {}

    vs_id = f"vs_{uuid.uuid4().hex}"
    store = {
        "id": vs_id,
        "object": "vector_store",
        "name": payload.get("name", "default-store"),
        "status": "ready",
    }
    VECTOR_STORES[vs_id] = store
    return JSONResponse(content=store, status_code=200)

# ---------------------------------------------------------------------
# List
# ---------------------------------------------------------------------
@router.get("")
async def list_vector_stores():
    """
    List all vector stores.
    Returns: {"object": "list", "data": [...]}
    """
    return JSONResponse(
        content={"object": "list", "data": list(VECTOR_STORES.values())},
        status_code=200,
    )

# ---------------------------------------------------------------------
# Retrieve
# ---------------------------------------------------------------------
@router.get("/{store_id}")
async def retrieve_vector_store(store_id: str):
    """
    Retrieve a single vector store by ID.
    Returns 404 if not found.
    """
    store = VECTOR_STORES.get(store_id)
    if not store:
        raise HTTPException(status_code=404, detail="Vector store not found")
    return JSONResponse(content=store, status_code=200)

# ---------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------
@router.delete("/{store_id}")
async def delete_vector_store(store_id: str):
    """
    Delete a vector store.
    Returns: {"deleted": true, "id": ...}
    """
    if store_id not in VECTOR_STORES:
        raise HTTPException(status_code=404, detail="Vector store not found")
    del VECTOR_STORES[store_id]
    return JSONResponse(content={"deleted": True, "id": store_id}, status_code=200)

# ---------------------------------------------------------------------
# Unsupported Methods
# ---------------------------------------------------------------------
@router.api_route("/{path:path}", methods=["PATCH", "PUT"])
async def unsupported_methods(path: str):
    """
    Return a 405 for unsupported update methods (PATCH / PUT).
    Mirrors the current OpenAI API, which does not yet allow updates.
    """
    raise HTTPException(status_code=405, detail="Method Not Allowed (PATCH/PUT not supported)")

# ---------------------------------------------------------------------
# Optional Forwarding (if you later wish to call upstream OpenAI)
# ---------------------------------------------------------------------
@router.api_route("/{path:path}", methods=["POST", "GET", "DELETE"], include_in_schema=False)
async def forward_if_configured(request: Request, path: str):
    """
    Optional: forward any real requests upstream if forward_openai_request
    is defined and the environment variable OPENAI_API_KEY is set.
    """
    if not forward_openai_request:
        raise HTTPException(status_code=501, detail="Upstream forwarding not configured")

    # Determine request type and forward accordingly
    method = request.method
    body = None
    try:
        if "application/json" in request.headers.get("content-type", ""):
            body = await request.json()
    except Exception:
        body = None

    result = await forward_openai_request(
        path=f"vector_stores/{path}",
        method=method,
        json=body,
        stream=False,
    )
    return result
