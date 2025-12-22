from __future__ import annotations

from fastapi import APIRouter, Request, Response

from app.api.forward_openai import forward_openai_request
from app.utils.logger import relay_log as logger

router = APIRouter(prefix="/v1", tags=["files"])


@router.get("/files")
async def list_files(request: Request) -> Response:
    """
    GET /v1/files
    Upstream: list files
    """
    logger.info("→ [files] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.post("/files")
async def create_file(request: Request) -> Response:
    """
    POST /v1/files
    Upstream expects multipart/form-data (file + purpose).
    We forward as-is.
    """
    logger.info("→ [files] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.get("/files/{file_id}")
async def retrieve_file(file_id: str, request: Request) -> Response:
    """
    GET /v1/files/{file_id}
    Upstream: retrieve file metadata
    """
    logger.info("→ [files] %s %s (file_id=%s)", request.method, request.url.path, file_id)
    return await forward_openai_request(request)


@router.delete("/files/{file_id}")
async def delete_file(file_id: str, request: Request) -> Response:
    """
    DELETE /v1/files/{file_id}
    Upstream: delete file
    """
    logger.info("→ [files] %s %s (file_id=%s)", request.method, request.url.path, file_id)
    return await forward_openai_request(request)


@router.get("/files/{file_id}/content")
async def retrieve_file_content_get(file_id: str, request: Request) -> Response:
    """
    GET /v1/files/{file_id}/content
    Upstream: retrieve file content (binary)
    """
    logger.info("→ [files] %s %s (file_id=%s)", request.method, request.url.path, file_id)
    return await forward_openai_request(request)


@router.head("/files/{file_id}/content", include_in_schema=False)
async def retrieve_file_content_head(file_id: str, request: Request) -> Response:
    """
    HEAD /v1/files/{file_id}/content

    HEAD is useful for clients, but it is not required for Actions/docs.
    We exclude it from OpenAPI to avoid duplicate operationId warnings.
    """
    logger.info("→ [files] %s %s (file_id=%s)", request.method, request.url.path, file_id)
    return await forward_openai_request(request)


@router.api_route(
    "/files/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"],
    include_in_schema=False,
)
async def files_passthrough(path: str, request: Request) -> Response:
    """
    Catch-all passthrough for future /v1/files/* endpoints.

    Kept out of OpenAPI to avoid operationId collisions and to keep
    the schema Actions-friendly.
    """
    logger.info("→ [files/*] %s %s (subpath=%s)", request.method, request.url.path, path)
    return await forward_openai_request(request)
