from __future__ import annotations

from fastapi import APIRouter, Request, Response

from app.api.forward_openai import forward_openai_request
from app.utils.logger import relay_log as logger

router = APIRouter(
    prefix="/v1",
    tags=["files"],
)


@router.get("/files")
async def list_files(request: Request) -> Response:
    """
    GET /v1/files
    List files (never returns raw binary).
    """
    logger.info("→ [files] GET %s", request.url.path)
    return await forward_openai_request(request)


@router.post("/files")
async def create_file(request: Request) -> Response:
    """
    POST /v1/files
    Create/upload a file.

    The relay forwards the multipart/form-data (or JSON) body as-is to
    the upstream OpenAI Files API.
    """
    logger.info("→ [files] POST %s", request.url.path)
    return await forward_openai_request(request)


@router.get("/files/{file_id}")
async def retrieve_file(file_id: str, request: Request) -> Response:
    """
    GET /v1/files/{file_id}
    Retrieve file metadata.
    """
    logger.info("→ [files] GET %s", request.url.path)
    return await forward_openai_request(request)


@router.delete("/files/{file_id}")
async def delete_file(file_id: str, request: Request) -> Response:
    """
    DELETE /v1/files/{file_id}
    Delete a file.
    """
    logger.info("→ [files] DELETE %s", request.url.path)
    return await forward_openai_request(request)


@router.get("/files/{file_id}/content")
async def retrieve_file_content(file_id: str, request: Request) -> Response:
    """
    GET /v1/files/{file_id}/content
    Stream / retrieve the raw file content.

    NOTE: This endpoint may return binary content, which the relay forwards
    untouched from OpenAI to the client.
    """
    logger.info("→ [files] GET %s (content)", request.url.path)
    return await forward_openai_request(request)
