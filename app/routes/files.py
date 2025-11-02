# ================================================================
# files.py — Handles file operations via OpenAI API
# ================================================================
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from app.api.forward_openai import forward_to_openai

router = APIRouter(prefix="/v1/files", tags=["files"])

@router.post("")
async def upload_file(request: Request):
    resp = await forward_to_openai(request, "/v1/files")
    return JSONResponse(resp.json(), status_code=resp.status_code)

@router.get("/{file_id}")
async def retrieve_file(file_id: str, request: Request):
    resp = await forward_to_openai(request, f"/v1/files/{file_id}")
    return JSONResponse(resp.json(), status_code=resp.status_code)

@router.get("/{file_id}/content")
async def retrieve_file_content(file_id: str, request: Request):
    resp = await forward_to_openai(request, f"/v1/files/{file_id}/content")
    # For file content, return text not JSON
    return JSONResponse(resp.json() if "application/json" in resp.headers.get("content-type", "") else {"content": resp.text})
