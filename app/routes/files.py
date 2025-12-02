# app/routes/files.py

from __future__ import annotations

from fastapi import APIRouter, Request, Response

from app.api.forward_openai import forward_openai_request

router = APIRouter(
    tags=["files"],
)


# ---------------------------------------------------------------------------
# Files API – https://platform.openai.com/docs/api-reference/files
# ---------------------------------------------------------------------------


@router.get("/v1/files")
async def list_files(request: Request) -> Response:
    """
    GET /v1/files

    List files stored in the OpenAI account.
    """
    return await forward_openai_request(request)


@router.post("/v1/files")
async def create_file(request: Request) -> Response:
    """
    POST /v1/files

    Create/upload a file. The body should be multipart/form-data as per
    OpenAI Files API.
    """
    return await forward_openai_request(request)


@router.get("/v1/files/{file_id}")
async def retrieve_file(file_id: str, request: Request) -> Response:
    """
    GET /v1/files/{file_id}

    Retrieve metadata for a single file.
    """
    return await forward_openai_request(request)


@router.delete("/v1/files/{file_id}")
async def delete_file(file_id: str, request: Request) -> Response:
    """
    DELETE /v1/files/{file_id}

    Delete a file by ID.
    """
    return await forward_openai_request(request)


@router.get("/v1/files/{file_id}/content")
async def retrieve_file_content(file_id: str, request: Request) -> Response:
    """
    GET /v1/files/{file_id}/content

    Download the raw contents of a file.
    """
    return await forward_openai_request(request)


# ---------------------------------------------------------------------------
# Uploads API – https://platform.openai.com/docs/api-reference/uploads
# ---------------------------------------------------------------------------


@router.post("/v1/uploads")
async def create_upload(request: Request) -> Response:
    """
    POST /v1/uploads

    Create a new upload (for large / multipart file uploads).
    """
    return await forward_openai_request(request)


@router.get("/v1/uploads/{upload_id}")
async def retrieve_upload(upload_id: str, request: Request) -> Response:
    """
    GET /v1/uploads/{upload_id}

    Retrieve an upload object by ID.
    """
    return await forward_openai_request(request)


@router.post("/v1/uploads/{upload_id}/complete")
async def complete_upload(upload_id: str, request: Request) -> Response:
    """
    POST /v1/uploads/{upload_id}/complete

    Mark a multipart upload as complete so it can be used by other APIs.
    """
    return await forward_openai_request(request)


@router.post("/v1/uploads/{upload_id}/cancel")
async def cancel_upload(upload_id: str, request: Request) -> Response:
    """
    POST /v1/uploads/{upload_id}/cancel

    Cancel an in-progress upload.
    """
    return await forward_openai_request(request)
