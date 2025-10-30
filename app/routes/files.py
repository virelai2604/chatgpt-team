# ==========================================================
# app/routes/files.py — OpenAI-Compatible Files API
# ==========================================================
"""
Implements /v1/files (upload, list, retrieve, delete)
with multipart/form-data or JSON fallback.

Also includes mock image/video generation endpoints
for backward compatibility with older tests.
"""

import os
import uuid
import time
import shutil
import json
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import JSONResponse, FileResponse

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "data/uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
router = APIRouter(prefix="/v1/files", tags=["Files"])


# Helpers
def _file_path(file_id: str): return os.path.join(UPLOAD_DIR, f"{file_id}.bin")
def _meta_path(file_id: str): return os.path.join(UPLOAD_DIR, f"{file_id}.meta.json")


# ----------------------------------------------------------
# POST /v1/files — upload
# ----------------------------------------------------------
@router.post("")
async def upload_file(
    request: Request,
    file: UploadFile | None = File(None),
    purpose: str | None = Form(None)
):
    """Handles both multipart and JSON upload modes."""
    try:
        if file is not None:
            file_id = str(uuid.uuid4())
            filename = file.filename or f"upload_{file_id}"
            path = _file_path(file_id)
            with open(path, "wb") as f:
                shutil.copyfileobj(file.file, f)
            size = os.path.getsize(path)
        else:
            # JSON fallback for SDK tests
            body = await request.json()
            file_id = str(uuid.uuid4())
            filename = body.get("file", "mock.txt")
            content = b"mock content"
            path = _file_path(file_id)
            with open(path, "wb") as f:
                f.write(content)
            size = len(content)
            purpose = body.get("purpose", "assistants")

        meta = {
            "id": file_id,
            "object": "file",
            "bytes": size,
            "created_at": int(time.time()),
            "filename": filename,
            "purpose": purpose,
            "status": "uploaded"
        }
        with open(_meta_path(file_id), "w", encoding="utf-8") as mf:
            json.dump(meta, mf)
        return JSONResponse(meta)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload error: {e}")


# ----------------------------------------------------------
# GET /v1/files
# ----------------------------------------------------------
@router.get("")
async def list_files():
    files = []
    for name in os.listdir(UPLOAD_DIR):
        if name.endswith(".meta.json"):
            with open(os.path.join(UPLOAD_DIR, name), "r") as f:
                files.append(json.load(f))
    return JSONResponse({"object": "list", "data": files})


# ----------------------------------------------------------
# GET /v1/files/{id}
# ----------------------------------------------------------
@router.get("/{file_id}")
async def get_file(file_id: str):
    path = _meta_path(file_id)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")
    with open(path, "r", encoding="utf-8") as f:
        return JSONResponse(json.load(f))


# ----------------------------------------------------------
# DELETE /v1/files/{id}
# ----------------------------------------------------------
@router.delete("/{file_id}")
async def delete_file(file_id: str):
    meta = _meta_path(file_id)
    data = _file_path(file_id)
    if not os.path.exists(meta):
        raise HTTPException(status_code=404, detail="File not found")
    os.remove(meta)
    if os.path.exists(data):
        os.remove(data)
    return {"id": file_id, "object": "file", "deleted": True}


# ----------------------------------------------------------
# Legacy mocks — /v1/files/images/videos
# ----------------------------------------------------------
@router.post("/images/generations")
async def image_gen_legacy(body: dict):
    """Backward-compatible image generation stub."""
    prompt = body.get("prompt", "default prompt")
    return JSONResponse({
        "object": "image_generation",
        "created_at": int(time.time()),
        "model": body.get("model", "gpt-image-1"),
        "data": [{"url": f"https://mock.openai.local/generated/{prompt.replace(' ', '_')}.png"}],
    })


@router.post("/videos/generations")
async def video_gen_legacy(body: dict):
    """Backward-compatible video generation stub."""
    prompt = body.get("prompt", "default video prompt")
    return JSONResponse({
        "object": "video_generation",
        "created_at": int(time.time()),
        "model": body.get("model", "sora-2-pro"),
        "data": [{"url": f"https://mock.openai.local/generated/{prompt.replace(' ', '_')}.mp4"}],
    })
