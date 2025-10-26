# ==========================================================
# app/routes/files.py — BIFL v2.3.4-fp
# ==========================================================
# Unified async file endpoint compatible with OpenAI /v1/files.
# Handles uploads, downloads, listing, and deletion.
# ==========================================================

from fastapi import APIRouter, Request
from app.api.forward import forward_openai
from app.utils.db_logger import log_event

router = APIRouter(prefix="/v1/files", tags=["Files"])

# ----------------------------------------------------------
# 📤  Upload File
# ----------------------------------------------------------
@router.post("")
async def upload_file(request: Request):
    """
    Upload a file to OpenAI (multipart/form-data supported).
    Example:
        POST /v1/files
        Content-Type: multipart/form-data
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
# 📥  Retrieve File
# ----------------------------------------------------------
@router.get("/{file_id}")
async def retrieve_file(request: Request, file_id: str):
    """Retrieve metadata or the file content itself."""
    endpoint = f"/v1/files/{file_id}"
    response = await forward_openai(request, endpoint)
    try:
        await log_event("/v1/files/retrieve", response.status_code, f"file {file_id}")
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
