# ==========================================================
# app/routes/videos.py — Legacy Sora Redirects (Full Future-Proof Set)
# BIFL v2.3.7-fp (Unified Sora-2 Pro migration)
# ==========================================================
# Implements /v1/videos, /v1/videos/remix, and /v1/videos/{id}
# All map to /v1/responses using function-based tools.
# ==========================================================

import os
import httpx
import json
from fastapi import APIRouter, Request, Response
from app.utils.error_handler import error_response

router = APIRouter(prefix="/v1/videos", tags=["Videos"])

# ----------------------------------------------------------
# 🔧 Config
# ----------------------------------------------------------
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
TIMEOUT = int(os.getenv("FORWARD_TIMEOUT", "600"))
DEFAULT_VIDEO_MODEL = os.getenv("VIDEO_MODEL", "sora-2-pro")

# ----------------------------------------------------------
# 🧩 Helpers
# ----------------------------------------------------------
def make_headers():
    return {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
        "OpenAI-Beta": "sora-2-pro=v2"
    }

async def post_to_openai(payload: dict):
    """Handle upstream POST to OpenAI /v1/responses with fallback for HTTP/2."""
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT, http2=True) as client:
            return await client.post(f"{OPENAI_BASE_URL}/v1/responses", headers=make_headers(), json=payload)
    except ImportError:
        async with httpx.AsyncClient(timeout=TIMEOUT, http2=False) as client:
            return await client.post(f"{OPENAI_BASE_URL}/v1/responses", headers=make_headers(), json=payload)


# ----------------------------------------------------------
# 🎬 /v1/videos → video_generate
# ----------------------------------------------------------
@router.post("")
async def create_video(request: Request):
    """Create video via Sora-2-Pro."""
    try:
        body = await request.json()
        model = body.get("model", DEFAULT_VIDEO_MODEL)
        prompt = body.get("prompt", "")
        seconds = body.get("seconds", 10)
        size = body.get("size", "1920x1080")
        stream = body.get("stream", True)

        payload = {
            "model": model,
            "input": prompt or f"Generate a {seconds}s {size} Sora-2-Pro video",
            "tools": [
                {
                    "type": "function",
                    "name": "video_generate",
                    "function": {
                        "description": "Generate a video clip using Sora 2 Pro",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "seconds": {"type": "integer", "default": seconds},
                                "size": {"type": "string", "default": size}
                            },
                            "required": ["seconds", "size"]
                        }
                    }
                }
            ],
            "stream": stream
        }

        upstream = await post_to_openai(payload)
        return Response(upstream.text, status_code=upstream.status_code,
                        media_type=upstream.headers.get("content-type", "application/json"))
    except Exception as e:
        return error_response("video_generate_error", str(e), 500)


# ----------------------------------------------------------
# 🎨 /v1/videos/remix → video_remix
# ----------------------------------------------------------
@router.post("/remix")
async def remix_video(request: Request):
    """Remix existing video using Sora 2 Pro."""
    try:
        body = await request.json()
        model = body.get("model", DEFAULT_VIDEO_MODEL)
        source_id = body.get("source_video_id")
        prompt = body.get("prompt", "")
        strength = body.get("strength", 0.6)

        if not source_id:
            return error_response("missing_parameter", "Missing source_video_id", 400)

        payload = {
            "model": model,
            "input": prompt or "Remix this video with a new prompt",
            "tools": [
                {
                    "type": "function",
                    "name": "video_remix",
                    "function": {
                        "description": "Remix an existing video using Sora 2 Pro",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "source_video_id": {"type": "string", "default": source_id},
                                "prompt": {"type": "string", "default": prompt},
                                "strength": {"type": "number", "default": strength}
                            },
                            "required": ["source_video_id", "prompt"]
                        }
                    }
                }
            ]
        }

        upstream = await post_to_openai(payload)
        return Response(upstream.text, status_code=upstream.status_code,
                        media_type=upstream.headers.get("content-type", "application/json"))
    except Exception as e:
        return error_response("video_remix_error", str(e), 500)


# ----------------------------------------------------------
# 📺 /v1/videos/{video_id} → video_status
# ----------------------------------------------------------
@router.get("/{video_id}")
async def get_video_status(video_id: str):
    """Fetch video generation or remix status."""
    try:
        payload = {
            "model": DEFAULT_VIDEO_MODEL,
            "input": f"Retrieve status of video {video_id}",
            "tools": [
                {
                    "type": "function",
                    "name": "video_status",
                    "function": {
                        "description": "Query generation or remix job status for Sora 2 Pro",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "video_id": {"type": "string", "default": video_id}
                            },
                            "required": ["video_id"]
                        }
                    }
                }
            ]
        }

        upstream = await post_to_openai(payload)
        return Response(upstream.text, status_code=upstream.status_code,
                        media_type=upstream.headers.get("content-type", "application/json"))
    except Exception as e:
        return error_response("video_status_error", str(e), 500)
