from fastapi import APIRouter, UploadFile, File, HTTPException, Response, Query
from app.utils.db_logger import save_attachment
from typing import List
import sqlite3
import hashlib
import uuid
from datetime import datetime
import getpass, socket

DB_PATH = r"D:\ChatgptDATAB\DB Chatgpt\chatgpt_archive.sqlite"
router = APIRouter()

@router.post("/upload")
async def upload_attachment(file: UploadFile = File(...)):
    content = await file.read()
    sha256 = hashlib.sha256(content).hexdigest()
    operator = getpass.getuser()
    machine = socket.gethostname()
    now = datetime.utcnow().isoformat()
    # Unique chat_id: sha256 prefix + uuid4
    chat_id = f"{sha256[:12]}-{uuid.uuid4().hex[:12]}"

    save_attachment(
        filename=file.filename,
        mimetype=file.content_type,
        size=len(content),
        sha256=sha256,
        data=content,
        imported_at=now,
        source_folder="api-upload",
        imported_by=operator,
        imported_on_machine=machine,
        replaced_at=None,
        chat_id=chat_id
    )
    return {"status": "ok", "sha256": sha256, "chat_id": chat_id}

@router.get("/{chat_id}/download")
async def download_attachment(chat_id: str):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT filename, mimetype, data FROM attachments WHERE chat_id=? ORDER BY version DESC LIMIT 1", (chat_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Attachment not found")
        filename, mimetype, data = row
        return Response(
            content=data,
            media_type=mimetype,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

@router.get("/list")
def list_attachments(limit: int = Query(25, gt=0, le=100)):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT chat_id, filename, mimetype, size, imported_at, version FROM attachments ORDER BY imported_at DESC LIMIT ?",
            (limit,)
        )
        rows = cur.fetchall()
        return [
            {
                "chat_id": r[0], "filename": r[1], "mimetype": r[2],
                "size": r[3], "imported_at": r[4], "version": r[5]
            }
            for r in rows
        ]

@router.delete("/{chat_id}")
def delete_attachment(chat_id: str):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM attachments WHERE chat_id=?", (chat_id,))
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Attachment not found")
    return {"status": "deleted", "chat_id": chat_id}
