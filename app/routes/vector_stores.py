"""
vector_stores.py — OpenAI-Compatible /v1/vector_stores Endpoint
────────────────────────────────────────────────────────────
Implements CRUD operations for vector stores exactly as defined in:
  • OpenAI API Reference (2025-10)
  • openai-python SDK v2.61
  • openai-node SDK v6.7.0

Supported endpoints:
  • POST   /v1/vector_stores              → create vector store
  • GET    /v1/vector_stores              → list vector stores
  • GET    /v1/vector_stores/{id}         → retrieve vector store
  • POST   /v1/vector_stores/{id}/files   → attach file(s)
  • DELETE /v1/vector_stores/{id}         → delete vector store
"""

import os
import httpx
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from app.utils.logger import log

router = APIRouter(prefix="/v1/vector_stores", tags=["vector_stores"])

OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
USER_AGENT = "openai-python/2.61.0"
RELAY_TIMEOUT = float(os.getenv("RELAY_TIMEOUT", 120))


# ------------------------------------------------------------
# Helper
# ------------------------------------------------------------
def build_headers(extra: dict | None = None) -> dict:
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "User-Agent": USER_AGENT,
        "Content-Type": "application/json",
    }
    if extra:
        headers.update(extra)
    return headers


async def forward(client: httpx.AsyncClient, method: str, endpoint: str, **kwargs):
    """Shared forwarding helper with SDK-style error schema."""
    try:
        resp = await client.request(
            method,
            f"{OPENAI_API_BASE}{endpoint}",
            headers=build_headers(),
            **kwargs,
        )
        return JSONResponse(resp.json(), status_code=resp.status_code)
    except httpx.RequestError as e:
        log.error(f"[VectorStores] Network error: {e}")
        return JSONResponse(
            {"error": {"message": str(e), "type": "network_error"}},
            status_code=502,
        )


# ------------------------------------------------------------
# POST /v1/vector_stores  → Create
# ------------------------------------------------------------
@router.post("")
async def create_vector_store(request: Request):
    """Create a new vector store."""
    body = await request.body()
    async with httpx.AsyncClient(timeout=RELAY_TIMEOUT) as client:
        return await forward(client, "POST", "/vector_stores", content=body)


# ------------------------------------------------------------
# GET /v1/vector_stores  → List
# ------------------------------------------------------------
@router.get("")
async def list_vector_stores():
    """List all vector stores for the organization."""
    async with httpx.AsyncClient(timeout=RELAY_TIMEOUT) as client:
        return await forward(client, "GET", "/vector_stores")


# ------------------------------------------------------------
# GET /v1/vector_stores/{id}  → Retrieve
# ------------------------------------------------------------
@router.get("/{vector_id}")
async def retrieve_vector_store(vector_id: str):
    """Retrieve a specific vector store by ID."""
    async with httpx.AsyncClient(timeout=RELAY_TIMEOUT) as client:
        return await forward(client, "GET", f"/vector_stores/{vector_id}")


# ------------------------------------------------------------
# POST /v1/vector_stores/{id}/files  → Attach file(s)
# ------------------------------------------------------------
@router.post("/{vector_id}/files")
async def attach_files_to_vector_store(vector_id: str, request: Request):
    """
    Attach one or more files to an existing vector store.
    Mirrors SDK call: client.vector_stores.files.create(vector_store_id=...)
    """
    content_type = request.headers.get("content-type", "")
    async with httpx.AsyncClient(timeout=RELAY_TIMEOUT) as client:
        try:
            if "multipart/form-data" in content_type:
                form = await request.form()
                files, data = [], {}
                for key, val in form.multi_items():
                    if hasattr(val, "filename"):
                        files.append((key, (val.filename, val.file, val.content_type)))
                    else:
                        data[key] = val

                resp = await client.post(
                    f"{OPENAI_API_BASE}/vector_stores/{vector_id}/files",
                    headers=build_headers({"Content-Type": content_type}),
                    files=files,
                    data=data,
                )
            else:
                body = await request.body()
                resp = await client.post(
                    f"{OPENAI_API_BASE}/vector_stores/{vector_id}/files",
                    headers=build_headers({"Content-Type": "application/json"}),
                    content=body,
                )

            return JSONResponse(resp.json(), status_code=resp.status_code)
        except httpx.RequestError as e:
            log.error(f"[VectorStores] File attach failed: {e}")
            return JSONResponse(
                {"error": {"message": str(e), "type": "network_error"}},
                status_code=502,
            )


# ------------------------------------------------------------
# DELETE /v1/vector_stores/{id}  → Delete
# ------------------------------------------------------------
@router.delete("/{vector_id}")
async def delete_vector_store(vector_id: str):
    """Delete a vector store."""
    async with httpx.AsyncClient(timeout=RELAY_TIMEOUT) as client:
        try:
            resp = await client.delete(
                f"{OPENAI_API_BASE}/vector_stores/{vector_id}",
                headers=build_headers(),
            )
            return JSONResponse(resp.json(), status_code=resp.status_code)
        except httpx.RequestError as e:
            log.error(f"[VectorStores] Delete failed: {e}")
            return JSONResponse(
                {"error": {"message": str(e), "type": "network_error"}},
                status_code=502,
            )
