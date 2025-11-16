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

OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


def build_headers():
    return {"Authorization": f"Bearer {OPENAI_API_KEY}"}


@router.post("")
async def upload_file(request: Request):
    """
    Proxy for POST /v1/files.

    NOTE:
      • As with embeddings, your orchestrator normally forwards this endpoint
        directly to OpenAI. This route is only used if /v1/files is excluded
        from the P4OrchestratorMiddleware forwarding.
    """
    async with httpx.AsyncClient() as client:
        if "multipart/form-data" in request.headers.get("content-type", ""):
            form = await request.form()
            files = [
                (k, (v.filename, v.file, v.content_type))
                for k, v in form.multi_items()
                if isinstance(v, UploadFile)
            ]
            resp = await client.post(
                f"{OPENAI_API_BASE.rstrip('/')}/v1/files",
                headers=build_headers(),
                files=files,
            )
        else:
            body = await request.body()
            resp = await client.post(
                f"{OPENAI_API_BASE.rstrip('/')}/v1/files",
                headers=build_headers(),
                content=body,
            )
        return JSONResponse(resp.json(), status_code=resp.status_code)
