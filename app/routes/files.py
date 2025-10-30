# ==========================================================
# app/routes/files.py — Ground Truth Edition (2025.10)
# ==========================================================
"""
Implements OpenAI-compatible file endpoints for relay proxy:

  - GET /v1/files               → listFiles
  - POST /v1/files              → uploadFile (multipart/form-data)
  - GET /v1/files/{file_id}     → getFile
  - DELETE /v1/files/{file_id}  → deleteFile
"""

import httpx
import logging
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from app.api.forward_openai import OPENAI_API_KEY, OPENAI_BASE_URL

router = APIRouter(tags=["Files"])


# ----------------------------------------------------------
# GET /v1/files — List all uploaded files
# ----------------------------------------------------------
@router.get("/v1/files")
async def list_files():
    """Lists all files uploaded under the current API key."""
    url = f"{OPENAI_BASE_URL}/v1/files"
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}

    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers)
        if resp.status_code >= 400:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        return JSONResponse(content=resp.json(), status_code=resp.status_code)


# ----------------------------------------------------------
# POST /v1/files — Upload file (multipart/form-data)
# ----------------------------------------------------------
@router.post("/v1/files")
async def upload_file(
    file: UploadFile = File(...),
    purpose: str = Form(default="user_data")
):
    """
    Uploads a file to OpenAI for later use by models or tools.
    Purpose can be one of: ['fine-tune', 'assistants', 'batch', 'user_data', 'evals', 'vision']
    """
    url = f"{OPENAI_BASE_URL}/v1/files"
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}

    try:
        # Prepare multipart upload form
        form_data = {
            "purpose": (None, purpose),
            "file": (file.filename, await file.read(), file.content_type or "application/octet-stream"),
        }

        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0)) as client:
            resp = await client.post(url, files=form_data, headers=headers)

        if resp.status_code >= 400:
            logging.error(f"[Relay] OpenAI Error {resp.status_code}: {resp.text}")
            raise HTTPException(status_code=resp.status_code, detail=resp.text)

        return JSONResponse(content=resp.json(), status_code=resp.status_code)

    except Exception as e:
        logging.exception(f"[Relay] Error uploading file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ----------------------------------------------------------
# GET /v1/files/{file_id} — Retrieve file metadata
# ----------------------------------------------------------
@router.get("/v1/files/{file_id}")
async def get_file(file_id: str):
    """Returns metadata for a specific uploaded file."""
    url = f"{OPENAI_BASE_URL}/v1/files/{file_id}"
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}

    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers)
        if resp.status_code >= 400:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        return JSONResponse(content=resp.json(), status_code=resp.status_code)


# ----------------------------------------------------------
# DELETE /v1/files/{file_id} — Delete file
# ----------------------------------------------------------
@router.delete("/v1/files/{file_id}")
async def delete_file(file_id: str):
    """Permanently removes a file from the system."""
    url = f"{OPENAI_BASE_URL}/v1/files/{file_id}"
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}

    async with httpx.AsyncClient() as client:
        resp = await client.delete(url, headers=headers)
        if resp.status_code >= 400:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        return JSONResponse(content=resp.json(), status_code=resp.status_code)
