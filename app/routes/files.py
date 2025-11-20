# app/routes/files.py

from fastapi import APIRouter, Request, UploadFile, File, Form
from fastapi.responses import Response

from app.api.forward_openai import (
    forward_openai_request,
    forward_multipart_to_openai,
)

router = APIRouter(prefix="/v1/files", tags=["files"])


@router.get("")
async def list_files(request: Request) -> Response:
    """
    Mirror OpenAI GET /v1/files
    """
    return await forward_openai_request(
        request=request,
        upstream_path="/files",
        method="GET",
    )


@router.post("")
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    purpose: str = Form(...),
) -> Response:
    """
    Mirror OpenAI POST /v1/files (multipart upload).
    """
    return await forward_multipart_to_openai(
        request=request,
        upstream_path="/files",
        file=file,
        purpose=purpose,
    )


@router.get("/{file_id}")
async def retrieve_file(file_id: str, request: Request) -> Response:
    """
    Mirror OpenAI GET /v1/files/{file_id}
    """
    return await forward_openai_request(
        request=request,
        upstream_path=f"/files/{file_id}",
        method="GET",
    )


@router.delete("/{file_id}")
async def delete_file(file_id: str, request: Request) -> Response:
    """
    Mirror OpenAI DELETE /v1/files/{file_id}
    """
    return await forward_openai_request(
        request=request,
        upstream_path=f"/files/{file_id}",
        method="DELETE",
    )


@router.get("/{file_id}/content")
async def download_file(file_id: str, request: Request) -> Response:
    """
    Mirror OpenAI GET /v1/files/{file_id}/content (binary payload).
    """
    return await forward_openai_request(
        request=request,
        upstream_path=f"/files/{file_id}/content",
        method="GET",
        stream_binary=True,
    )
