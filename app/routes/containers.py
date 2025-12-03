# app/routes/containers.py

from __future__ import annotations

from fastapi import APIRouter, Request, Response

from app.api.forward_openai import forward_openai_request
from app.utils.logger import relay_log as logger

router = APIRouter(
    prefix="/v1",
    tags=["containers"],
)


@router.api_route("/containers", methods=["GET", "POST", "HEAD", "OPTIONS"])
async def containers_root(request: Request) -> Response:
    """
    - POST /v1/containers → create container
    - GET  /v1/containers → list containers
    """
    logger.info("→ [containers] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.api_route(
    "/containers/{path:path}",
    methods=["GET", "POST", "DELETE", "HEAD", "OPTIONS"],
)
async def containers_subpaths(path: str, request: Request) -> Response:
    """
    Catch-all for /v1/containers/*, including:

      - /v1/containers/{container_id}
      - /v1/containers/{container_id}/files
      - /v1/containers/{container_id}/files/{file_id}/content
    """
    logger.info("→ [containers/*] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)
