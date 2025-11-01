"""
files.py — /v1/files
Handles file uploads, downloads, and metadata listing.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, JSONResponse
import os
import uuid
import time
from app.utils.logger import logger

UPLOAD_DIR = "data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

router = APIRouter()

@router.post("/v1/files")
async def upload_file(file: UploadFile = File(...)):
    file_id = f"file_{uuid.uuid4().hex[:12]}"
    path = os.path.join(UPLOAD_DIR, file_id)
    with open(path, "wb") as f:
        content = await file.read()
        f.write(content)
    meta = {
        "id": file_id,
        "object": "file",
        "created": int(time.time()),
        "filename": file.filename,
        "bytes": len(content),
        "purpose": "upload"
    }
    logger.info(f"Uploaded file {file_id}")
    return JSONResponse(meta)

@router.get("/v1/files")
async def list_files():
    files = []
    for name in os.listdir(UPLOAD_DIR):
        path = os.path.join(UPLOAD_DIR, name)
        files.append({
            "id": name,
            "object": "file",
            "bytes": os.path.getsize(path),
            "created": int(os.path.getctime(path))
        })
    return {"object": "list", "data": files}

@router.get("/v1/files/{file_id}")
async def get_file_metadata(file_id: str):
    path = os.path.join(UPLOAD_DIR, file_id)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")
    return {
        "id": file_id,
        "object": "file",
        "bytes": os.path.getsize(path),
        "created": int(os.path.getctime(path))
    }

@router.get("/v1/files/{file_id}/content")
async def download_file(file_id: str):
    path = os.path.join(UPLOAD_DIR, file_id)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path, filename=file_id)

@router.delete("/v1/files/{file_id}")
async def delete_file(file_id: str):
    path = os.path.join(UPLOAD_DIR, file_id)
    if os.path.exists(path):
        os.remove(path)
        logger.info(f"Deleted file {file_id}")
    return {"id": file_id, "object": "file", "deleted": True}
