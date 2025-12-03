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
    Videos root.

    Covers:
      - POST /v1/videos      (create job)
      - GET  /v1/videos      (list jobs, per current docs)
    """
    logger.info("→ [videos] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.api_route(
    "/videos/{path:path}",
    methods=["GET", "POST", "DELETE", "HEAD", "OPTIONS"],
)
async def proxy_videos_subpaths(path: str, request: Request) -> Response:
    """
    Catch-all for video-related subresources.

    Examples:
      - POST   /v1/videos/remix
      - GET    /v1/videos/{video_id}
      - GET    /v1/videos/{video_id}/content
      - DELETE /v1/videos/{video_id}
      - any future /v1/videos/* additions
    """
    logger.info("→ [videos/*] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)
