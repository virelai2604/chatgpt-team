from __future__ import annotations

from fastapi import APIRouter, Request, Response

from app.api.forward_openai import forward_openai_request
from app.utils.logger import relay_log as logger

router = APIRouter(
    prefix="/v1",
    tags=["containers"],
)


@router.api_route(
    "/containers",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"],
)
async def proxy_containers_root(request: Request) -> Response:
    """
    Generic proxy for /v1/containers.
    """
    logger.info("→ [containers] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.api_route(
    "/containers/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"],
)
async def proxy_containers_subpaths(path: str, request: Request) -> Response:
    """
    Generic proxy for any /v1/containers/* sub-path, including `/file`.
    """
    logger.info("→ [containers/*] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)
