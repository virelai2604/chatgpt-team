from __future__ import annotations

import logging

from fastapi import APIRouter, Request, Response

from app.api.forward_openai import forward_openai_request

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/v1",
    tags=["videos"],
)


@router.post("/videos")
async def create_video(request: Request) -> Response:
    """
    POST /v1/videos

    Create a video generation job.
    Mirrors:
    https://platform.openai.com/docs/api-reference/videos
    """
    logger.debug("Proxying POST /v1/videos to OpenAI")
    return await forward_openai_request(request)


@router.get("/videos")
async def list_videos(request: Request) -> Response:
    """
    GET /v1/videos

    List video jobs.
    """
    logger.debug("Proxying GET /v1/videos to OpenAI")
    return await forward_openai_request(request)


@router.get("/videos/{video_id}")
async def retrieve_video(video_id: str, request: Request) -> Response:
    """
    GET /v1/videos/{video_id}

    Retrieve a video job.
    """
    logger.debug("Proxying GET /v1/videos/%s to OpenAI", video_id)
    return await forward_openai_request(request)


@router.delete("/videos/{video_id}")
async def delete_video(video_id: str, request: Request) -> Response:
    """
    DELETE /v1/videos/{video_id}

    Delete a video job.
    """
    logger.debug("Proxying DELETE /v1/videos/%s to OpenAI", video_id)
    return await forward_openai_request(request)


@router.get("/videos/{video_id}/content")
async def download_video_content(video_id: str, request: Request) -> Response:
    """
    GET /v1/videos/{video_id}/content

    Download rendered video content.
    """
    logger.debug("Proxying GET /v1/videos/%s/content to OpenAI", video_id)
    return await forward_openai_request(request)


@router.post("/videos/{video_id}/remix")
async def remix_video(video_id: str, request: Request) -> Response:
    """
    POST /v1/videos/{video_id}/remix

    Remix a completed video job.
    """
    logger.debug("Proxying POST /v1/videos/%s/remix to OpenAI", video_id)
    return await forward_openai_request(request)
