# app/routes/files.py

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
    logger.info("→ [files] GET %s", request.url.path)
    return await forward_openai_request(request)


@router.post("/files")
async def create_file(request: Request) -> Response:
    logger.info("→ [files] POST %s", request.url.path)
    return await forward_openai_request(request)


@router.get("/files/{file_id}")
async def retrieve_file(file_id: str, request: Request) -> Response:
    logger.info("→ [files] GET %s", request.url.path)
    return await forward_openai_request(request)


@router.delete("/files/{file_id}")
async def delete_file(file_id: str, request: Request) -> Response:
    logger.info("→ [files] DELETE %s", request.url.path)
    return await forward_openai_request(request)


@router.get("/files/{file_id}/content")
async def download_file_content(file_id: str, request: Request) -> Response:
    """
    Proxy for /v1/files/{file_id}/content – returns binary file content.
    """
    logger.info("→ [files/content] GET %s", request.url.path)
    return await forward_openai_request(request)


@router.api_route(
    "/files/{path:path}",
    methods=["GET", "POST", "DELETE", "HEAD", "OPTIONS"],
)
async def files_subpaths(path: str, request: Request) -> Response:
    """
    Catch-all for any additional /v1/files/* subroutes.
    """
    logger.info("→ [files/*] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)
