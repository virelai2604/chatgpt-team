# ==========================================================
# app/routes/files.py — Ground Truth Compliant Implementation
# ==========================================================
"""
Implements OpenAI-compatible /v1/files endpoints (2025.11).

Handles file uploads, listing, retrieval, deletion, and content download.
Also includes 307 redirects for legacy image/video generation routes
to their new canonical locations under /v1/responses/tools/*.
"""

import os
import uuid
import time
import shutil
import json
import logging
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import JSONResponse, FileResponse, RedirectResponse

router = APIRouter(prefix="/v1/files", tags=["Files"])
logger = logging.getLogger("files")

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "data/uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


def _file_path(file_id: str, filename: str | None = None) -> str:
    if filename:
        return os.path.join(UPLOAD_DIR, f"{file_id}_{filename}")
    return os.path.join(UPLOAD_DIR, f"{file_id}.bin")

def _meta_path(file_id: str) -> str:
    return os.path.join(UPLOAD_DIR, f"{file_id}.meta.json")


@router.post("")
async def upload_file(
    request: Request,
    file: UploadFile | None = File(None),
    purpose: str | None = Form(None)
):
    """Upload file with multipart or JSON fallback."""
    try:
        file_id = str(uuid.uuid4())
        filename = None
        bytes_written = 0

        if file is not None:
            filename = file.filename or f"upload_{file_id}"
            filepath = _file_path(file_id, filename)
            with open(filepath, "wb") as f:
                shutil.copyfileobj(file.file, f)
            bytes_written = os.path.getsize(filepath)
        else:
            try:
                body = await request.json()
            except Exception:
                raise HTTPException(status_code=400, detail="Invalid JSON upload.")
            filename = body.get("file", f"mock_{file_id}.txt")
            filepath = _file_path(file_id, filename)
            content = body.get("content", "mock content").encode()
            with open(filepath, "wb") as f:
                f.write(content)
            bytes_written = len(content)
            purpose = body.get("purpose", "assistants")

        metadata = {
            "id": file_id,
            "object": "file",
            "bytes": bytes_written,
            "created_at": int(time.time()),
            "filename": filename,
            "purpose": purpose or "assistants"
        }

        with open(_meta_path(file_id), "w", encoding="utf-8") as meta_file:
            json.dump(metadata, meta_file)

        return JSONResponse(metadata)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload error: {e}")


@router.get("")
async def list_files():
    """List all uploaded files."""
    files = []
    for name in os.listdir(UPLOAD_DIR):
        if name.endswith(".meta.json"):
            try:
                with open(os.path.join(UPLOAD_DIR, name), "r", encoding="utf-8") as f:
                    files.append(json.load(f))
            except Exception:
                continue
    return JSONResponse({"object": "list", "data": files})


@router.get("/{file_id}")
async def get_file(file_id: str):
    """Retrieve metadata for a file."""
    path = _meta_path(file_id)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")
    with open(path, "r", encoding="utf-8") as f:
        return JSONResponse(json.load(f))


@router.get("/{file_id}/content")
async def download_file(file_id: str):
    """Download file content."""
    for name in os.listdir(UPLOAD_DIR):
        if name.startswith(file_id) and not name.endswith(".meta.json"):
            return FileResponse(os.path.join(UPLOAD_DIR, name))
    raise HTTPException(status_code=404, detail="File content not found")


@router.delete("/{file_id}")
async def delete_file(file_id: str):
    """Deletes both metadata and binary file."""
    meta_path = _meta_path(file_id)
    if not os.path.exists(meta_path):
        raise HTTPException(status_code=404, detail="File not found")

    os.remove(meta_path)
    for name in os.listdir(UPLOAD_DIR):
        if name.startswith(file_id) and not name.endswith(".meta.json"):
            os.remove(os.path.join(UPLOAD_DIR, name))

    return JSONResponse({"id": file_id, "object": "file", "deleted": True})


# ----------------------------------------------------------
# Legacy redirects (sunset)
# ----------------------------------------------------------
@router.post("/images/generations")
async def legacy_image_redirect():
    logger.warning("⚠️ Deprecated route: redirecting /v1/files/images/generations → /v1/responses/tools/image_generation")
    return RedirectResponse(url="/v1/responses/tools/image_generation", status_code=307)

@router.post("/videos/generations")
async def legacy_video_redirect():
    logger.warning("⚠️ Deprecated route: redirecting /v1/files/videos/generations → /v1/responses/tools/video_generation")
    return RedirectResponse(url="/v1/responses/tools/video_generation", status_code=307)
