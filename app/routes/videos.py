"""
videos.py — /v1/videos
───────────────────────
Thin proxy for OpenAI Video (Sora) API.

The OpenAI REST API surface for videos is:

  POST /v1/videos       -> create a video generation job
  GET  /v1/videos/{id}  -> get job status and result URLs

This router keeps the FastAPI endpoints OpenAI-compatible and delegates
all network I/O to forward_openai_request.
"""

from fastapi import APIRouter, Request
from app.api.forward_openai import forward_openai_request
from app.utils.logger import relay_log as logger

router = APIRouter(prefix="/v1/videos", tags=["videos"])


@router.post("")
async def create_video(request: Request):
    """
    POST /v1/videos
    Creates a video generation job (Sora / gpt-sora-2, etc).
    """
    try:
        body = await request.json()
        model = body.get("model")
    except Exception:
        model = None

    logger.info(f"[Videos] create_video model={model!r}")
    return await forward_openai_request(request)


@router.get("/{video_id}")
async def get_video(video_id: str, request: Request):
    """
    GET /v1/videos/{video_id}
    Retrieves job status and result URLs.
    """
    logger.info(f"[Videos] get_video id={video_id}")
    return await forward_openai_request(request)
