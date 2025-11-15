"""
files.py — /v1/files
─────────────────────
Handles uploads, listing, retrieval, content streaming, and deletion.
"""

import os
import httpx
from fastapi import APIRouter, Request, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse

router = APIRouter(prefix="/v1/files", tags=["files"])

OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def build_headers():
    return {"Authorization": f"Bearer {OPENAI_API_KEY}"}

@router.post("")
async def upload_file(request: Request):
    async with httpx.AsyncClient() as client:
        if "multipart/form-data" in request.headers.get("content-type", ""):
            form = await request.form()
            files = [(k, (v.filename, v.file, v.content_type))
                     for k, v in form.multi_items() if isinstance(v, UploadFile)]
            resp = await client.post(f"{OPENAI_API_BASE}/files", headers=build_headers(), files=files)
        else:
            body = await request.body()
            resp = await client.post(f"{OPENAI_API_BASE}/files", headers=build_headers(), content=body)
        return JSONResponse(resp.json(), status_code=resp.status_code)
