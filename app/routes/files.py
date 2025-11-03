"""
files.py — OpenAI-Compatible /v1/files Endpoint
────────────────────────────────────────────────────────────
Implements all file management operations exactly like
OpenAI SDK v2.61 and Node SDK v6.7.0.

Conforms to:
  • POST /v1/files        — multipart/form-data upload
  • GET /v1/files         — list files
  • GET /v1/files/{id}    — retrieve metadata
  • GET /v1/files/{id}/content — download file contents
  • DELETE /v1/files/{id} — delete file
"""

import os
import httpx
from fastapi import APIRouter, Request, UploadFile, Form
from fastapi.responses import JSONResponse, StreamingResponse
from app.utils.logger import log

router = APIRouter(prefix="/v1/files", tags=["files"])

OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
USER_AGENT = "openai-python/2.61.0"
RELAY_TIMEOUT = float(os.getenv("RELAY_TIMEOUT", 120))

# ------------------------------------------------------------
# Helper
# ------------------------------------------------------------
def build_headers():
    return {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "User-Agent": USER_AGENT,
    }


# ------------------------------------------------------------
# POST /v1/files  → Upload
# ------------------------------------------------------------
@router.post("")
async def upload_file(request: Request):
    """Uploads a file via multipart/form-data."""
    headers = build_headers()

    content_type = request.headers.get("content-type", "")
    async with httpx.AsyncClient(timeout=RELAY_TIMEOUT) as client:
        try:
            if "multipart/form-data" in content_type:
                form = await request.form()
                files = []
                data = {}
                for key, value in form.multi_items():
                    if isinstance(value, UploadFile):
                        files.append((key, (value.filename, value.file, value.content_type)))
                    else:
                        data[key] = value
                resp = await client.post(f"{OPENAI_API_BASE}/files", headers=headers, data=data, files=files)
            else:
                body = await request.body()
                resp = await client.post(
                    f"{OPENAI_API_BASE}/files",
                    headers={**headers, "Content-Type": "application/json"},
                    content=body,
                )

            return JSONResponse(resp.json(), status_code=resp.status_code)

        except httpx.RequestError as e:
            log.error(f"[Files] Upload error: {e}")
            return JSONResponse({"error": {"message": str(e), "type": "network_error"}}, status_code=502)


# ------------------------------------------------------------
# GET /v1/files → List files
# ------------------------------------------------------------
@router.get("")
async def list_files():
    headers = build_headers()
    async with httpx.AsyncClient(timeout=RELAY_TIMEOUT) as client:
        try:
            resp = await client.get(f"{OPENAI_API_BASE}/files", headers=headers)
            return JSONResponse(resp.json(), status_code=resp.status_code)
        except httpx.RequestError as e:
            return JSONResponse({"error": {"message": str(e), "type": "network_error"}}, status_code=502)


# ------------------------------------------------------------
# GET /v1/files/{file_id} → Metadata
# ------------------------------------------------------------
@router.get("/{file_id}")
async def retrieve_file(file_id: str):
    headers = build_headers()
    async with httpx.AsyncClient(timeout=RELAY_TIMEOUT) as client:
        try:
            resp = await client.get(f"{OPENAI_API_BASE}/files/{file_id}", headers=headers)
            return JSONResponse(resp.json(), status_code=resp.status_code)
        except httpx.RequestError as e:
            return JSONResponse({"error": {"message": str(e), "type": "network_error"}}, status_code=502)


# ------------------------------------------------------------
# GET /v1/files/{file_id}/content → Download
# ------------------------------------------------------------
@router.get("/{file_id}/content")
async def retrieve_file_content(file_id: str, request: Request):
    headers = build_headers()
    async with httpx.AsyncClient(timeout=None) as client:
        try:
            resp = await client.get(f"{OPENAI_API_BASE}/files/{file_id}/content", headers=headers)
            if "text/event-stream" in resp.headers.get("content-type", ""):
                async def sse_stream():
                    async for chunk in resp.aiter_bytes():
                        if await request.is_disconnected():
                            log.info("[Files] client disconnected during file stream")
                            break
                        yield chunk
                return StreamingResponse(sse_stream(), media_type="text/event-stream")

            return StreamingResponse(resp.aiter_bytes(), media_type=resp.headers.get("content-type"))
        except httpx.RequestError as e:
            return JSONResponse({"error": {"message": str(e), "type": "network_error"}}, status_code=502)


# ------------------------------------------------------------
# DELETE /v1/files/{file_id}
# ------------------------------------------------------------
@router.delete("/{file_id}")
async def delete_file(file_id: str):
    headers = build_headers()
    async with httpx.AsyncClient(timeout=RELAY_TIMEOUT) as client:
        try:
            resp = await client.delete(f"{OPENAI_API_BASE}/files/{file_id}", headers=headers)
            return JSONResponse(resp.json(), status_code=resp.status_code)
        except httpx.RequestError as e:
            return JSONResponse({"error": {"message": str(e), "type": "network_error"}}, status_code=502)
