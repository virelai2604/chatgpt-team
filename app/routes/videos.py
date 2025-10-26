# ==========================================================
# app/routes/videos.py — BIFL v2.3.4-fp (finalized)
# ==========================================================
# OpenAI-compatible video generation + job proxy.
# Supports Sora 2 Pro, GPT-5 video tools, and async streaming.
# ==========================================================

from fastapi import APIRouter, Request
from app.api.forward import forward_openai
from app.utils.db_logger import log_event

router = APIRouter(prefix="/v1/videos", tags=["Videos"])

# ----------------------------------------------------------
# 🎬  Generate Video (stream-enabled)
# ----------------------------------------------------------
@router.post("")
async def generate_video(request: Request):
    """
    Create a new video generation job.
    Supports streaming progress logs via NDJSON.

    Example:
      {
        "model": "sora-2-pro",
        "prompt": "A flying dragon made of fire",
        "seconds": 10,
        "size": "1920x1080",
        "stream": true
      }
    """
    endpoint = "/v1/responses?tools=video_generation"
    response = await forward_openai(request, endpoint)
    try:
        await log_event("/v1/videos", response.status_code, "video generation started")
    except Exception:
        pass
    return response


# ----------------------------------------------------------
# 🔍  Get Video Job Status
# ----------------------------------------------------------
@router.get("/{job_id}")
async def get_video_job(request: Request, job_id: str):
    """
    Retrieve metadata or progress for a specific video job.
    Streams progress updates when available.
    """
    endpoint = f"/v1/videos/{job_id}"
    response = await forward_openai(request, endpoint)
    try:
        await log_event(endpoint, response.status_code, f"video job {job_id}")
    except Exception:
        pass
    return response


# ----------------------------------------------------------
# 🧹  Delete / Cancel Video Job
# ----------------------------------------------------------
@router.delete("/{job_id}")
async def cancel_video_job(request: Request, job_id: str):
    """
    Cancel or delete a video generation job.
    """
    endpoint = f"/v1/videos/{job_id}"
    response = await forward_openai(request, endpoint)
    try:
        await log_event(endpoint, response.status_code, f"cancel job {job_id}")
    except Exception:
        pass
    return response
