# app/routes/videos.py
from __future__ import annotations

from fastapi import APIRouter, Request, Response

from app.api.forward_openai import forward_openai_request
from app.utils.logger import relay_log as logger

router = APIRouter(
    prefix="/v1",
    tags=["videos"],
)


@router.post("/videos")
async def create_video(request: Request) -> Response:
    """
    POST /v1/videos

    Create a new video generation or editing job.
    """
    logger.info("→ [videos] POST %s", request.url.path)
    return await forward_openai_request(request)


@router.get("/videos")
async def list_videos(request: Request) -> Response:
    """
    GET /v1/videos

    List video jobs.
    """
    logger.info("→ [videos] GET %s", request.url.path)
    return await forward_openai_request(request)


@router.post("/videos/remix")
async def remix_video(request: Request) -> Response:
    """
    POST /v1/videos/remix

    Remix an existing video.
    """
    logger.info("→ [videos] POST %s", request.url.path)
    return await forward_openai_request(request)


@router.post("/videos/edits")
async def edit_video(request: Request) -> Response:
    """
    POST /v1/videos/edits

    Edit an existing video (if supported by upstream API).
    """
    logger.info("→ [videos] POST %s", request.url.path)
    return await forward_openai_request(request)


@router.get("/videos/{video_id}")
async def retrieve_video(video_id: str, request: Request) -> Response:
    """
    GET /v1/videos/{video_id}

    Retrieve video job metadata.
    """
    logger.info("→ [videos] GET %s", request.url.path)
    return await forward_openai_request(request)


@router.delete("/videos/{video_id}")
async def delete_video(video_id: str, request: Request) -> Response:
    """
    DELETE /v1/videos/{video_id}

    Delete a video job (if supported).
    """
    logger.info("→ [videos] DELETE %s", request.url.path)
    return await forward_openai_request(request)


@router.get("/videos/{video_id}/content")
async def retrieve_video_content(video_id: str, request: Request) -> Response:
    """
    GET /v1/videos/{video_id}/content

    Retrieve rendered video content.
    """
    logger.info("→ [videos] GET %s", request.url.path)
    return await forward_openai_request(request)


@router.api_route(
    "/videos/{path:path}",
    methods=["GET", "POST", "DELETE", "HEAD", "OPTIONS"],
)
async def proxy_videos_subpaths(path: str, request: Request) -> Response:
    """
    Catch-all proxy for any future /v1/videos/* subpaths.

    This keeps the relay compatible with future Video API additions
    without code changes.
    """
    logger.info("→ [videos/*] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)
