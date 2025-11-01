# ==========================================================
# app/routes/files.py — OpenAI-Compatible Files API (v2025.11)
# ==========================================================
"""
Implements /v1/files endpoints for upload, listing, retrieval, and deletion.
Fully compatible with OpenAI REST API and openai-python SDK behavior.

Supports both:
  - Local mock file registry (for relay mode)
  - Upstream passthrough to OpenAI API (FORWARD_MODE)
"""

import os
import uuid
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from fastapi.responses import JSONResponse
from app.api.forward_openai import forward_openai_request

router = APIRouter(tags=["Files"])

# Local file store (for mock relay mode)
FILES_REGISTRY = {}
UPLOAD_DIR = os.path.join("data", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

FORWARD_MODE = os.getenv("FORWARD_FILES_TO_OPENAI", "false").lower() == "true"


# ----------------------------------------------------------
# Helper: Serialize a file entry in OpenAI schema format
# ----------------------------------------------------------
def serialize_file_entry(fid: str, entry: dict):
    return {
        "id": fid,
        "object": "file",
        "bytes": entry.get("bytes", 0),
        "created_at": entry.get("created_at"),
        "filename": entry.get("filename"),
        "purpose": entry.get("purpose", "assistants"),
        "status": entry.get("status", "uploaded"),
    }


# ----------------------------------------------------------
# POST /v1/files — Upload a file
# ----------------------------------------------------------
@router.post("/files", summary="Upload a file", status_code=200)
async def upload_file(request: Request, file: UploadFile = File(...)):
    """
    Uploads a file compatible with OpenAI's /v1/files.

    If FORWARD_MODE=True, forwards the upload to OpenAI.
    Otherwise, stores it locally in ./data/uploads.
    """
    if FORWARD_MODE:
        # Forward to OpenAI directly (multipart)
        return await forward_openai_request("/v1/files", body=None, stream=False)

    try:
        content = await file.read()
        file_id = f"file_{uuid.uuid4().hex[:8]}"
        file_path = os.path.join(UPLOAD_DIR, file.filename)

        with open(file_path, "wb") as f:
            f.write(content)

        entry = {
            "id": file_id,
            "filename": file.filename,
            "bytes": len(content),
            "purpose": "assistants",
            "created_at": int(datetime.now().timestamp()),
            "status": "uploaded",
            "path": file_path,
        }
        FILES_REGISTRY[file_id] = entry

        return JSONResponse(content=serialize_file_entry(file_id, entry), status_code=200)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File upload failed: {e}")


# ----------------------------------------------------------
# GET /v1/files — List all uploaded files
# ----------------------------------------------------------
@router.get("/files", summary="List uploaded files")
async def list_files():
    """
    Returns all locally uploaded files (mock relay mode).
    """
    if FORWARD_MODE:
        return await forward_openai_request("/v1/files", body=None, stream=False)

    data = [serialize_file_entry(fid, entry) for fid, entry in FILES_REGISTRY.items()]
    return JSONResponse(content={"object": "list", "data": data})


# ----------------------------------------------------------
# GET /v1/files/{file_id} — Retrieve file metadata
# ----------------------------------------------------------
@router.get("/files/{file_id}", summary="Retrieve file metadata")
async def retrieve_file(file_id: str):
    """
    Returns metadata for a specific uploaded file.
    """
    if FORWARD_MODE:
        return await forward_openai_request(f"/v1/files/{file_id}", body=None, stream=False)

    if file_id not in FILES_REGISTRY:
        raise HTTPException(status_code=404, detail="File not found")

    entry = FILES_REGISTRY[file_id]
    return JSONResponse(content=serialize_file_entry(file_id, entry))


# ----------------------------------------------------------
# DELETE /v1/files/{file_id} — Delete file
# ----------------------------------------------------------
@router.delete("/files/{file_id}", summary="Delete file")
async def delete_file(file_id: str):
    """
    Deletes a file locally or forwards delete to OpenAI.
    """
    if FORWARD_MODE:
        return await forward_openai_request(f"/v1/files/{file_id}", body=None, stream=False)

    entry = FILES_REGISTRY.pop(file_id, None)
    if not entry:
        raise HTTPException(status_code=404, detail="File not found")

    try:
        if os.path.exists(entry["path"]):
            os.remove(entry["path"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File deletion failed: {e}")

    return JSONResponse(content={"id": file_id, "object": "file", "deleted": True})


# ----------------------------------------------------------
# GET /v1/files/{file_id}/content — Download file content
# ----------------------------------------------------------
@router.get("/files/{file_id}/content", summary="Download file content")
async def get_file_content(file_id: str):
    """
    Downloads raw file content from local relay store.
    """
    if FORWARD_MODE:
        return await forward_openai_request(f"/v1/files/{file_id}/content", body=None, stream=False)

    entry = FILES_REGISTRY.get(file_id)
    if not entry or not os.path.exists(entry["path"]):
        raise HTTPException(status_code=404, detail="File not found")

    try:
        with open(entry["path"], "rb") as f:
            data = f.read()
        return JSONResponse(
            content={
                "id": file_id,
                "filename": entry["filename"],
                "content": data.decode(errors="ignore"),
                "bytes": entry["bytes"],
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {e}")
