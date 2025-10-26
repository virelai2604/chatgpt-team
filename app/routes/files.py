# app/routes/files.py
# BIFL v2.2 — Hybrid Local/Relay File API
# Handles file upload, metadata retrieval, and content streaming.
# Compatible with OpenAI SDK 2.6.1 and GPT-5-Codex relay models.

import os
import uuid
import time
import aiofiles
import sqlite3
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from typing import Optional, Dict, Any, List
from app.api.forward import forward_openai


router = APIRouter(prefix="/v1/files", tags=["Files"])

# === Config ===
FILES_DIR = os.getenv("FILES_DIR", "data/files")
DB_PATH = os.path.join(FILES_DIR, "files.db")
os.makedirs(FILES_DIR, exist_ok=True)

# === Init DB ===
def init_db():
    with sqlite3.connect(DB_PATH) as db:
        db.execute("""
        CREATE TABLE IF NOT EXISTS files (
            id TEXT PRIMARY KEY,
            filename TEXT,
            bytes INTEGER,
            file_id TEXT,
            purpose TEXT,
            created_at INTEGER
        );
        """)
init_db()

# === Utilities ===
def save_metadata(filename: str, size: int, purpose: str, file_id: Optional[str] = None):
    with sqlite3.connect(DB_PATH) as db:
        db.execute(
            "INSERT INTO files (id, filename, bytes, file_id, purpose, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), filename, size, file_id, purpose, int(time.time())),
        )
        db.commit()

def list_metadata() -> List[Dict[str, Any]]:
    with sqlite3.connect(DB_PATH) as db:
        rows = db.execute("SELECT id, filename, bytes, file_id, purpose, created_at FROM files ORDER BY created_at DESC").fetchall()
        return [
            {"id": r[0], "object": "file", "filename": r[1], "bytes": r[2], "file_id": r[3],
             "purpose": r[4], "created_at": r[5]}
            for r in rows
        ]


# === Routes ===

@router.get("/")
async def list_files():
    """List locally known files (hybrid with relay support)."""
    files = list_metadata()
    return JSONResponse(content={"object": "list", "data": files})


@router.post("/")
async def upload_file(file: UploadFile = File(...), purpose: str = "assistants"):
    """Upload file locally, mirror to /v1/files relay, and store metadata."""
    try:
        os.makedirs(FILES_DIR, exist_ok=True)
        local_path = os.path.join(FILES_DIR, file.filename)
        async with aiofiles.open(local_path, "wb") as f:
            content = await file.read()
            await f.write(content)

        size = os.path.getsize(local_path)
        file_id = None

        try:
            relay_resp = await forward_openai(
                path="/v1/files",
                method="POST",
                files={"file": (file.filename, open(local_path, "rb"))},
                data={"purpose": purpose}
            )
            file_id = relay_resp.get("id") if relay_resp else None
        except Exception as e:
            print(f"[WARN] Relay upload failed for {file.filename}: {e}")

        save_metadata(file.filename, size, purpose, file_id)

        return JSONResponse(
            status_code=200,
            content={
                "object": "file",
                "filename": file.filename,
                "bytes": size,
                "purpose": purpose,
                "file_id": file_id,
                "local_path": local_path,
                "relay_synced": bool(file_id),
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File upload failed: {e}")


@router.get("/{file_id}")
async def get_file_metadata(file_id: str):
    """Retrieve file metadata by local ID or remote file_id."""
    with sqlite3.connect(DB_PATH) as db:
        row = db.execute("SELECT id, filename, bytes, file_id, purpose, created_at FROM files WHERE id = ? OR file_id = ?", (file_id, file_id)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="File not found")

    return JSONResponse(content={
        "object": "file",
        "id": row[0],
        "filename": row[1],
        "bytes": row[2],
        "file_id": row[3],
        "purpose": row[4],
        "created_at": row[5],
    })


@router.get("/{file_id}/content")
async def download_file(file_id: str):
    """Download file content from local cache; fallback to relay if missing."""
    # Try local lookup first
    with sqlite3.connect(DB_PATH) as db:
        row = db.execute("SELECT filename, file_id FROM files WHERE id = ? OR file_id = ?", (file_id, file_id)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="File metadata not found")

    filename, relay_id = row
    path = os.path.join(FILES_DIR, filename)

    # Serve from disk if present
    if os.path.exists(path):
        async def stream_file():
            async with aiofiles.open(path, "rb") as f:
                chunk = await f.read(8192)
                while chunk:
                    yield chunk
                    chunk = await f.read(8192)
        return StreamingResponse(stream_file(), media_type="application/octet-stream")

    # Otherwise fetch from relay
    try:
        relay_resp = await forward_openai(path=f"/v1/files/{relay_id}/content", method="GET")
        if not relay_resp:
            raise HTTPException(status_code=404, detail="File missing both locally and remotely")
        return StreamingResponse(iter([relay_resp]), media_type="application/octet-stream")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Relay fetch failed: {e}")


@router.delete("/{file_id}")
async def delete_file(file_id: str):
    """Delete file locally and attempt remote deletion."""
    with sqlite3.connect(DB_PATH) as db:
        row = db.execute("SELECT filename, file_id FROM files WHERE id = ? OR file_id = ?", (file_id, file_id)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="File not found")
        filename, relay_id = row

    # Delete local file
    local_path = os.path.join(FILES_DIR, filename)
    if os.path.exists(local_path):
        os.remove(local_path)

    # Delete metadata
    with sqlite3.connect(DB_PATH) as db:
        db.execute("DELETE FROM files WHERE id = ? OR file_id = ?", (file_id, file_id))
        db.commit()

    # Attempt remote deletion
    try:
        await forward_openai(path=f"/v1/files/{relay_id}", method="DELETE")
    except Exception as e:
        print(f"[WARN] Relay deletion failed for {relay_id}: {e}")

    return JSONResponse(content={"deleted": file_id, "relay_id": relay_id})
