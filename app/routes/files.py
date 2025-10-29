# ==========================================================
# app/routes/files.py — Relay v2025-10 Ground Truth Mirror
# ==========================================================
# OpenAI-compatible /v1/files endpoint for uploads, listing,
# retrieval, content download, and deletion.
# Fully async, DB-logged, and proxy-safe for streaming.
# ==========================================================

from fastapi import APIRouter, Request
from app.api.forward_openai import forward_openai


router = APIRouter(prefix="/v1/files", tags=["Files"])

# ----------------------------------------------------------
# 📤  Upload File
# ----------------------------------------------------------
@router.post("")
async def upload_file(request: Request):
    """
    Upload a file to OpenAI (multipart/form-data supported).
    Mirrors POST /v1/files.
    """
    response = await forward_openai(request, "/v1/files")
    try:
        await log_event("/v1/files/upload", response.status_code, "file upload")
    except Exception:
        pass
    return response


# ----------------------------------------------------------
# 📄  List Files
# ----------------------------------------------------------
@router.get("")
async def list_files(request: Request):
    """List files available in the account or organization."""
    response = await forward_openai(request, "/v1/files")
    try:
        await log_event("/v1/files/list", response.status_code, "file list")
    except Exception:
        pass
    return response


# ----------------------------------------------------------
# 📥  Retrieve File Metadata
# ----------------------------------------------------------
@router.get("/{file_id}")
async def retrieve_file(request: Request, file_id: str):
    """Retrieve file metadata."""
    endpoint = f"/v1/files/{file_id}"
    response = await forward_openai(request, endpoint)
    try:
        await log_event("/v1/files/retrieve", response.status_code, f"file {file_id}")
    except Exception:
        pass
    return response


# ----------------------------------------------------------
# 📂  Retrieve File Content
# ----------------------------------------------------------
@router.get("/{file_id}/content")
async def retrieve_file_content(request: Request, file_id: str):
    """Download the raw content of a file."""
    endpoint = f"/v1/files/{file_id}/content"
    response = await forward_openai(request, endpoint)
    try:
        await log_event(endpoint, response.status_code, f"download {file_id}")
    except Exception:
        pass
    return response


# ----------------------------------------------------------
# 🗑️  Delete File
# ----------------------------------------------------------
@router.delete("/{file_id}")
async def delete_file(request: Request, file_id: str):
    """Delete a file upstream."""
    endpoint = f"/v1/files/{file_id}"
    response = await forward_openai(request, endpoint)
    try:
        await log_event("/v1/files/delete", response.status_code, f"file {file_id}")
    except Exception:
        pass
    return response
