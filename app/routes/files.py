# app/routes/files.py

from fastapi import APIRouter, Request

from app.api.forward_openai import forward_openai_request

router = APIRouter(prefix="/v1/files", tags=["files"])


@router.get("")
async def list_files(request: Request):
    """
    List files: GET /v1/files

    Simple JSON GET, no body – proxied directly.
    """
    return await forward_openai_request(
        request=request,
        path="/files",
        method="GET",
    )


@router.post("")
async def create_file(request: Request):
    """
    Create/upload file: POST /v1/files

    - For multipart/form-data (file uploads): forward raw body bytes to OpenAI.
    - For JSON (rare, e.g. future extensions): forward as JSON.
    """

    content_type = request.headers.get("content-type", "")

    # Multipart upload (curl -F ...) – do NOT parse, just forward raw
    if content_type.lower().startswith("multipart/form-data"):
        raw_body: bytes = await request.body()
        return await forward_openai_request(
            request=request,
            path="/files",
            method="POST",
            raw_body=raw_body,
            content_type=content_type,
        )

    # Fallback: try JSON if not multipart
    try:
        json_body = await request.json()
    except Exception:
        json_body = None

    return await forward_openai_request(
        request=request,
        path="/files",
        method="POST",
        json_body=json_body,
        content_type=request.headers.get("content-type"),
    )


@router.get("/{file_id}")
async def retrieve_file(request: Request, file_id: str):
    """
    Retrieve a single file's metadata: GET /v1/files/{file_id}
    """
    return await forward_openai_request(
        request=request,
        path=f"/files/{file_id}",
        method="GET",
    )


@router.delete("/{file_id}")
async def delete_file(request: Request, file_id: str):
    """
    Delete a file: DELETE /v1/files/{file_id}
    """
    return await forward_openai_request(
        request=request,
        path=f"/files/{file_id}",
        method="DELETE",
    )


@router.get("/{file_id}/content")
async def download_file_content(request: Request, file_id: str):
    """
    Download file contents: GET /v1/files/{file_id}/content

    Note: OpenAI returns the raw file bytes; forward_openai_request will
    preserve the content-type and stream it back.
    """
    return await forward_openai_request(
        request=request,
        path=f"/files/{file_id}/content",
        method="GET",
    )
