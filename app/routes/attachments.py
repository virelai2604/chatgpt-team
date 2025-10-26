# app/routes/attachments.py
# BIFL v2.2 — Hybrid Local/Relay File Attachments API
# Supports local persistence + automatic registration via /v1/files relay.

import os
import uuid
import time
import sqlite3
import aiofiles
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from typing import List, Dict, Any, Optional
from app.api.forward import forward_openai


router = APIRouter(prefix="/v1/attachments", tags=["Attachments"])

# === Config ===
ATTACHMENTS_DIR = os.getenv("ATTACHMENTS_DIR", "data/uploads")
DB_PATH = os.path.join(ATTACHMENTS_DIR, "attachments.db")
os.makedirs(ATTACHMENTS_DIR, exist_ok=True)

# === Init local DB ===
def init_db():
    with sqlite3.connect(DB_PATH) as db:
        db.execute("""
        CREATE TABLE IF NOT EXISTS attachments (
            id TEXT PRIMARY KEY,
            chat_id TEXT,
            filename TEXT,
            bytes INTEGER,
            file_id TEXT,
            created_at INTEGER
        );
        """)
init_db()


# === Utility ===
def save_metadata(chat_id: str, filename: str, size: int, file_id: Optional[str] = None):
    with sqlite3.connect(DB_PATH) as db:
        db.execute(
            "INSERT INTO attachments (id, chat_id, filename, bytes, file_id, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), chat_id, filename, size, file_id, int(time.time()))
        )
        db.commit()


def list_metadata(chat_id: str) -> List[Dict[str, Any]]:
    with sqlite3.connect(DB_PATH) as db:
        rows = db.execute(
            "SELECT id, filename, bytes, file_id, created_at FROM attachments WHERE chat_id = ? ORDER BY created_at DESC",
            (chat_id,)
        ).fetchall()
        return [
            {
                "id": row[0],
                "object": "file",
                "filename": row[1],
                "bytes": row[2],
                "file_id": row[3],
                "created_at": row[4],
                "chat_id": chat_id
            } for row in rows
        ]


def delete_metadata(chat_id: str, filename: str):
    with sqlite3.connect(DB_PATH) as db:
        db.execute("DELETE FROM attachments WHERE chat_id = ? AND filename = ?", (chat_id, filename))
        db.commit()


# === Endpoints ===

@router.post("/{chat_id}/upload")
async def upload_attachment(
    chat_id: str,
    file: UploadFile = File(...),
    relay: bool = Form(True)
):
    """Upload a file locally and (optionally) register it via OpenAI /v1/files."""
    upload_dir = os.path.join(ATTACHMENTS_DIR, chat_id)
    os.makedirs(upload_dir, exist_ok=True)

    local_path = os.path.join(upload_dir, file.filename)
    try:
        # 1️⃣ Save locally
        async with aiofiles.open(local_path, "wb") as out_file:
            content = await file.read()
            await out_file.write(content)
        size = os.path.getsize(local_path)

        file_id = None
        # 2️⃣ Optionally register remotely
        if relay:
            try:
                relay_resp = await forward_openai(
                    path="/v1/files",
                    method="POST",
                    files={"file": (file.filename, open(local_path, "rb"))}
                )
                if relay_resp and "id" in relay_resp:
                    file_id = relay_resp["id"]
            except Exception as e:
                print(f"[WARN] Relay upload failed: {e}")

        # 3️⃣ Save metadata
        save_metadata(chat_id, file.filename, size, file_id)

        return JSONResponse(
            status_code=200,
            content={
                "object": "file",
                "filename": file.filename,
                "bytes": size,
                "chat_id": chat_id,
                "file_id": file_id,
                "local_path": local_path,
                "relay_synced": bool(file_id)
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {e}")


@router.get("/{chat_id}")
async def list_attachments(chat_id: str):
    """List all attachments for a chat."""
    files = list_metadata(chat_id)
    return JSONResponse(content={"object": "list", "data": files})


@router.get("/{chat_id}/download/{filename}")
async def download_attachment(chat_id: str, filename: str):
    """Download a locally stored attachment."""
    path = os.path.join(ATTACHMENTS_DIR, chat_id, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")

    async def file_stream():
        async with aiofiles.open(path, "rb") as f:
            chunk = await f.read(8192)
            while chunk:
                yield chunk
                chunk = await f.read(8192)

    headers = {"Content-Disposition": f"attachment; filename={filename}"}
    return StreamingResponse(file_stream(), headers=headers, media_type="application/octet-stream")


@router.delete("/{chat_id}/{filename}")
async def delete_attachment(chat_id: str, filename: str):
    """Delete an attachment locally and remove from metadata DB."""
    path = os.path.join(ATTACHMENTS_DIR, chat_id, filename)
    if os.path.exists(path):
        os.remove(path)
    delete_metadata(chat_id, filename)
    return JSONResponse(content={"deleted": filename, "chat_id": chat_id})


# === Optional: sync missing local→relay ===
@router.post("/{chat_id}/sync")
async def sync_missing(chat_id: str):
    """Force re-upload of missing local files to relay."""
    upload_dir = os.path.join(ATTACHMENTS_DIR, chat_id)
    if not os.path.exists(upload_dir):
        return JSONResponse(content={"synced": 0, "message": "No local directory"})
    synced = 0
    for fname in os.listdir(upload_dir):
        path = os.path.join(upload_dir, fname)
        try:
            relay_resp = await forward_openai(
                path="/v1/files",
                method="POST",
                files={"file": (fname, open(path, "rb"))}
            )
            if relay_resp and "id" in relay_resp:
                save_metadata(chat_id, fname, os.path.getsize(path), relay_resp["id"])
                synced += 1
        except Exception as e:
            print(f"[SYNC WARN] {fname}: {e}")
    return JSONResponse(content={"synced": synced})
