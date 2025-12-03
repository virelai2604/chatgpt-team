# app/routes/files.py
from __future__ import annotations

from fastapi import APIRouter, Request, Response

from app.api.forward_openai import forward_openai_request
from app.utils.logger import relay_log as logger  # type: ignore

router = APIRouter(
    prefix="/v1",
    tags=["files"],
)


@router.get("/files")
async def list_files(request: Request) -> Response:
    """
    GET /v1/files
    List files.
    """
    logger.info("[files] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.post("/files")
async def create_file(request: Request) -> Response:
    """
    POST /v1/files
    Create a file (JSON → multipart handled upstream).
    """
    logger.info("[files] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.get("/files/{file_id}")
async def retrieve_file(file_id: str, request: Request) -> Response:
    """
    GET /v1/files/{file_id}
    Retrieve metadata for a file.
    """
    logger.info("[files] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.delete("/files/{file_id}")
async def delete_file(file_id: str, request: Request) -> Response:
    """
    DELETE /v1/files/{file_id}
    Delete a file.
    """
    logger.info("[files] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.post("/uploads")
async def create_upload(request: Request) -> Response:
    """
    POST /v1/uploads
    Proxy for the OpenAI uploads API used by /v1/files.
    """
    logger.info("[files/uploads] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)
