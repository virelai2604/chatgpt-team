# app/routes/videos.py

from __future__ import annotations

from fastapi import APIRouter, Request, Response

from app.api.forward_openai import forward_openai_request
from app.utils.logger import relay_log as logger

router = APIRouter(
    prefix="/v1",
    tags=["videos"],
)


@router.api_route("/videos", methods=["GET", "POST", "HEAD", "OPTIONS"])
async def proxy_videos_root(request: Request) -> Response:
    """
    - POST /v1/videos           → create video job
    - GET /v1/videos            → list video jobs
    """
    logger.info("→ [videos] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.api_route(
    "/videos/{path:path}",
    methods=["GET", "POST", "DELETE", "HEAD", "OPTIONS"],
)
async def proxy_videos_subpaths(path: str, request: Request) -> Response:
    """
    Catch-all for /v1/videos/*, including:

      - /v1/videos/{video_id}
      - /v1/videos/{video_id}/content
      - /v1/videos/remix
      - /v1/videos/job
    """
    logger.info("→ [videos/*] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)
