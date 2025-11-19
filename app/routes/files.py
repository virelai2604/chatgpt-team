# app/routes/files.py
from fastapi import APIRouter, Request

from app.api.forward_openai import forward_openai_request

router = APIRouter(prefix="/v1/files", tags=["files"])


@router.get("")
async def list_files(request: Request):
    """
    List files – forwards GET /v1/files to OpenAI.
    Simple JSON GET, no body – proxied directly.
    """
    return await forward_openai_request(
        request=request,
        method="GET",
    )


@router.post("")
async def create_file(request: Request):
    """
    Create/upload file – forwards POST /v1/files.

    - For multipart/form-data (file uploads): forward raw body bytes to OpenAI.
    - For JSON (rare, e.g. future extensions): forward as JSON.
    """
    content_type = request.headers.get("content-type", "")

    # Multipart upload (curl -F ...) – do NOT parse, just forward raw body
    if content_type.lower().startswith("multipart/form-data"):
        raw_body: bytes = await request.body()
        return await forward_openai_request(
            request=request,
            method="POST",
            raw_body=raw_body,
            content_type=content_type,
        )

    # JSON body fallback (not typical for /v1/files, but safe)
    try:
        json_body = await request.json()
    except Exception:
        json_body = None

    return await forward_openai_request(
        request=request,
        method="POST",
        json=json_body,
    )


@router.get("/{file_id}")
async def retrieve_file(request: Request, file_id: str):
    """
    Retrieve a single file's metadata – forwards GET /v1/files/{file_id}.
    The path and query string are preserved automatically by the forwarder.
    """
    return await forward_openai_request(
        request=request,
        method="GET",
    )


@router.delete("/{file_id}")
async def delete_file(request: Request, file_id: str):
    """
    Delete a file – forwards DELETE /v1/files/{file_id}.
    """
    return await forward_openai_request(
        request=request,
        method="DELETE",
    )
