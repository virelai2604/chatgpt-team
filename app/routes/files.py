"""
files.py — /v1/files
────────────────────
Thin proxy for file upload/list/retrieve/delete against OpenAI.

Matches the official Files API:
  • GET    /v1/files
  • POST   /v1/files
  • GET    /v1/files/{file_id}
  • GET    /v1/files/{file_id}/content
  • DELETE /v1/files/{file_id}
"""

import os

import httpx
from fastapi import APIRouter, UploadFile, File
from fastapi.responses import JSONResponse, Response

from app.utils.logger import relay_log as log

router = APIRouter(prefix="/v1/files", tags=["files"])

OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_ORG_ID = os.getenv("OPENAI_ORG_ID", "")
RELAY_TIMEOUT = float(os.getenv("RELAY_TIMEOUT", "60"))


def auth_headers() -> dict:
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    if OPENAI_ORG_ID:
        headers["OpenAI-Organization"] = OPENAI_ORG_ID
    return headers


def files_base_url() -> str:
    return f"{OPENAI_API_BASE.rstrip('/')}/v1/files"


@router.get("")
async def list_files():
    async with httpx.AsyncClient(timeout=RELAY_TIMEOUT) as client:
        resp = await client.get(files_base_url(), headers=auth_headers())
        return JSONResponse(resp.json(), status_code=resp.status_code)


@router.post("")
async def upload_file(file: UploadFile = File(...), purpose: str = "assistants"):
    files = {"file": (file.filename, await file.read(), file.content_type)}
    data = {"purpose": purpose}
    async with httpx.AsyncClient(timeout=RELAY_TIMEOUT) as client:
        resp = await client.post(
            files_base_url(),
            headers=auth_headers(),
            files=files,
            data=data,
        )
        return JSONResponse(resp.json(), status_code=resp.status_code)


@router.get("/{file_id}")
async def retrieve_file(file_id: str):
    async with httpx.AsyncClient(timeout=RELAY_TIMEOUT) as client:
        resp = await client.get(
            f"{files_base_url()}/{file_id}",
            headers=auth_headers(),
        )
        return JSONResponse(resp.json(), status_code=resp.status_code)


@router.get("/{file_id}/content")
async def download_file_content(file_id: str):
    async with httpx.AsyncClient(timeout=RELAY_TIMEOUT) as client:
        resp = await client.get(
            f"{files_base_url()}/{file_id}/content",
            headers=auth_headers(),
        )
        return Response(content=resp.content, status_code=resp.status_code)


@router.delete("/{file_id}")
async def delete_file(file_id: str):
    async with httpx.AsyncClient(timeout=RELAY_TIMEOUT) as client:
        resp = await client.delete(
            f"{files_base_url()}/{file_id}",
            headers=auth_headers(),
        )
        return JSONResponse(resp.json(), status_code=resp.status_code)
