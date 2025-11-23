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

    Generic proxy for the videos root. This will forward:
      - GET /v1/videos
      - POST /v1/videos
    directly to the upstream OpenAI /v1/videos endpoint.
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

    Generic proxy for any nested video path, including:
      - POST /v1/videos/generations
      - GET  /v1/videos/{video_id}
      - GET  /v1/videos/{video_id}/content
      - DELETE /v1/videos/{video_id}

    All are forwarded to the upstream OpenAI API unchanged
    except for auth/headers handled in forward_openai_request.
    """
    logger.info(
        "→ [videos] %s %s (subpath=%s)",
        request.method,
        request.url.path,
        path,
    )
    return await forward_openai_request(request)
