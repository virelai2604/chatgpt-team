"""
files.py — /v1/files
────────────────────
Thin proxy for file upload/list/retrieve/delete against OpenAI.
"""

import os
import httpx
from fastapi import APIRouter, UploadFile, File
from fastapi.responses import JSONResponse, Response

from app.utils.logger import relay_log as log

router = APIRouter(prefix="/v1/files", tags=["files"])

OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


def auth_headers():
    return {"Authorization": f"Bearer {OPENAI_API_KEY}"}


@router.get("")
async def list_files():
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.get(f"{OPENAI_API_BASE.rstrip('/')}/files", headers=auth_headers())
        return JSONResponse(resp.json(), status_code=resp.status_code)


@router.post("")
async def upload_file(file: UploadFile = File(...), purpose: str = "assistants"):
    files = {"file": (file.filename, await file.read(), file.content_type)}
    data = {"purpose": purpose}
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            f"{OPENAI_API_BASE.rstrip('/')}/files",
            headers=auth_headers(),
            files=files,
            data=data,
        )
        return JSONResponse(resp.json(), status_code=resp.status_code)


@router.get("/{file_id}")
async def retrieve_file(file_id: str):
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.get(
            f"{OPENAI_API_BASE.rstrip('/')}/files/{file_id}",
            headers=auth_headers(),
        )
        return JSONResponse(resp.json(), status_code=resp.status_code)


@router.get("/{file_id}/content")
async def download_file_content(file_id: str):
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.get(
            f"{OPENAI_API_BASE.rstrip('/')}/files/{file_id}/content",
            headers=auth_headers(),
        )
        return Response(content=resp.content, status_code=resp.status_code)


@router.delete("/{file_id}")
async def delete_file(file_id: str):
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.delete(
            f"{OPENAI_API_BASE.rstrip('/')}/files/{file_id}",
            headers=auth_headers(),
        )
        return JSONResponse(resp.json(), status_code=resp.status_code)
