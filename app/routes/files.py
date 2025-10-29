# ==========================================================
# app/routes/files.py — Ground Truth OpenAI-Compatible Mirror
# ==========================================================
from fastapi import APIRouter, UploadFile, File
from fastapi.responses import JSONResponse
from app.api.forward_openai import forward_openai_request

router = APIRouter(prefix="/v1/files", tags=["Files"])

@router.get("")
async def list_files():
    """
    Mirrors OpenAI GET /v1/files
    Lists all uploaded files for the current API key.
    """
    result = await forward_openai_request("v1/files", method="GET")
    return JSONResponse(result)

@router.post("")
async def upload_file(file: UploadFile = File(...)):
    """
    Mirrors OpenAI POST /v1/files
    Upload a file. This relay implementation transmits filename and content
    as JSON text for simplicity. Binary-safe multipart proxying can be added later.
    """
    content = await file.read()
    data = {
        "filename": file.filename,
        "content": content.decode(errors="ignore"),
    }
    result = await forward_openai_request("v1/files", method="POST", json_data=data)
    return JSONResponse(result)

@router.get("/{file_id}")
async def retrieve_file(file_id: str):
    """
    Mirrors OpenAI GET /v1/files/{file_id}
    Retrieves metadata for a specific file.
    """
    result = await forward_openai_request(f"v1/files/{file_id}", method="GET")
    return JSONResponse(result)

@router.get("/{file_id}/content")
async def retrieve_file_content(file_id: str):
    """
    Mirrors OpenAI GET /v1/files/{file_id}/content
    Streams or returns the raw file content.
    """
    result = await forward_openai_request(f"v1/files/{file_id}/content", method="GET")
    return JSONResponse(result)

@router.delete("/{file_id}")
async def delete_file(file_id: str):
    """
    Mirrors OpenAI DELETE /v1/files/{file_id}
    Deletes a file permanently.
    """
    result = await forward_openai_request(f"v1/files/{file_id}", method="DELETE")
    return JSONResponse(result)
