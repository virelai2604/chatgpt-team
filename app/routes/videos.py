"""
videos.py — /v1/videos
───────────────────────
Thin proxy for OpenAI Video (Sora) API.

The API supports:
  POST /v1/videos      -> create a video generation job
  GET  /v1/videos/{id} -> get job status and result URLs
"""

import os
import httpx
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/v1/videos", tags=["videos"])

OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TIMEOUT = float(os.getenv("RELAY_TIMEOUT", "300"))


def _headers():
    return {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }


@router.post("")
async def create_video(request: Request):
    """
    POST /v1/videos
    Creates a video generation job.
    """
    body = await request.json()
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.post(
            f"{OPENAI_API_BASE.rstrip('/')}/videos",
            headers=_headers(),
            json=body,
        )
        return JSONResponse(resp.json(), status_code=resp.status_code)


@router.get("/{video_id}")
async def get_video(video_id: str):
    """
    GET /v1/videos/{video_id}
    Retrieves job status and result URLs.
    """
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.get(
            f"{OPENAI_API_BASE.rstrip('/')}/videos/{video_id}",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
        )
        return JSONResponse(resp.json(), status_code=resp.status_code)
