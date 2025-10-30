# ==========================================================
# files.py — File Management Routes
# ==========================================================
"""
Relays OpenAI file operations via /v1/files endpoints.
Adds 'purpose' automatically to comply with 2025.10 API spec.
"""

from fastapi import APIRouter, UploadFile, File
from app.api.forward_openai import forward_openai_request

router = APIRouter(prefix="/v1/files", tags=["Files"])


@router.get("")
async def list_files():
    """List uploaded files."""
    return await forward_openai_request("v1/files", "GET")


@router.post("")
async def upload_file(file: UploadFile = File(...)):
    """Upload a new file (purpose=responses)."""
    files = {"file": (file.filename, file.file, file.content_type)}
    data = {"purpose": "responses"}  # ✅ required by OpenAI now
    return await forward_openai_request("v1/files", "POST", data=data, files=files)


@router.get("/{file_id}")
async def get_file(file_id: str):
    """Retrieve metadata for a specific file."""
    return await forward_openai_request(f"v1/files/{file_id}", "GET")


@router.delete("/{file_id}")
async def delete_file(file_id: str):
    """Delete a file."""
    return await forward_openai_request(f"v1/files/{file_id}", "DELETE")
