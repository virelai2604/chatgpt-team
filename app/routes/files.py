# app/routes/files.py

from __future__ import annotations

from fastapi import APIRouter, Request, Response

from app.api.forward_openai import forward_openai_request
from app.utils.logger import relay_log as logger

router = APIRouter(
    prefix="/v1",
    tags=["files"],
)


@router.api_route("/files", methods=["GET", "POST", "HEAD", "OPTIONS"])
async def proxy_files_root(request: Request) -> Response:
    """
    Files root.

    Covers:
      - GET  /v1/files   (list)
      - POST /v1/files   (create/upload)
    """
    logger.info("→ [files] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.api_route(
    "/files/{path:path}",
    methods=["GET", "POST", "DELETE", "HEAD", "OPTIONS"],
)
async def proxy_files_subpaths(path: str, request: Request) -> Response:
    """
    Catch-all for Files subresources.

    Examples:
      - GET    /v1/files/{file_id}
      - DELETE /v1/files/{file_id}
      - GET    /v1/files/{file_id}/content
      - future /v1/files/* additions (e.g. uploads interoperability)
    """
    logger.info("→ [files/*] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)
