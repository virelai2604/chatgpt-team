from __future__ import annotations

from fastapi import APIRouter, Request

from app.api.forward_openai import forward_openai_request
from app.utils.logger import relay_log as logger

router = APIRouter(
    prefix="/v1",
    tags=["videos"],
)


@router.api_route("/videos", methods=["GET", "POST", "HEAD", "OPTIONS"])
async def proxy_videos_root(request: Request):
    """
    /v1/videos
    """
    logger.info("→ [videos] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.api_route(
    "/videos/{path:path}",
    methods=["GET", "POST", "DELETE", "HEAD", "OPTIONS"],
)
async def proxy_videos_subpaths(path: str, request: Request):
    """
    /v1/videos/{...}
    """
    logger.info(
        "→ [videos] %s %s (subpath=%s)",
        request.method,
        request.url.path,
        path,
    )
    return await forward_openai_request(request)
