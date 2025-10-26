# ==========================================================
# app/routes/videos.py — Sora 2 Pro Integration (Auto JSON / Multipart)
# BIFL v2.3.9-fp (Future-Proof)
# ==========================================================
# Handles both JSON and multipart input automatically.
# Supports:
#   POST   /v1/videos                → Create video (JSON or form)
#   POST   /v1/videos/{id}/remix     → Remix existing video
#   GET    /v1/videos/{id}           → Get metadata
#   GET    /v1/videos/{id}/content   → Stream MP4
# ==========================================================

import os
import httpx
from fastapi import APIRouter, Request, Response
from app.utils.error_handler import error_response

router = APIRouter(prefix="/v1/videos", tags=["Videos"])

OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_ORG_ID = os.getenv("OPENAI_ORG_ID", "")
TIMEOUT = int(os.getenv("FORWARD_TIMEOUT", "600"))
DEFAULT_MODEL = os.getenv("VIDEO_MODEL", "sora-2-pro")

# ──────────────────────────────────────────────
# Build headers for all Sora API requests
# ──────────────────────────────────────────────
def _headers() -> dict:
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "OpenAI-Beta": "sora-2-pro=v2",
    }
    if OPENAI_ORG_ID:
        headers["OpenAI-Organization"] = OPENAI_ORG_ID
    return headers


# ==========================================================
# 🎬 Create Video (JSON or Multipart)
# ==========================================================
@router.post("")
async def create_video(request: Request):
    """
    Create a Sora 2 Pro video.
    Accepts JSON or multipart/form-data, converts both to proper multipart
    before forwarding to OpenAI /v1/videos.
    """
    try:
        # Detect content type
        content_type = request.headers.get("content-type", "")
        form_data = {}

        if "application/json" in content_type:
            body = await request.json()
            form_data = {
                "model": body.get("model", DEFAULT_MODEL),
                "prompt": body.get("prompt", ""),
                "seconds": str(body.get("seconds", 8)),
                "size": body.get("size", "1024x1024"),
            }
        else:
            # Fallback: parse as multipart or urlencoded
            form = await request.form()
            form_data = {
                "model": form.get("model", DEFAULT_MODEL),
                "prompt": form.get("prompt", ""),
                "seconds": str(form.get("seconds", 8)),
                "size": form.get("size", "1024x1024"),
            }

        # Sanity check
        if not form_data["prompt"]:
            return error_response("missing_field", "Field 'prompt' is required", 400)

        # Forward to OpenAI (always multipart/form-data)
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.post(
                f"{OPENAI_BASE_URL}/v1/videos",
                headers=_headers(),
                data=form_data,
            )

        return Response(
            content=resp.text,
            media_type=resp.headers.get("content-type", "application/json"),
            status_code=resp.status_code,
        )

    except httpx.RequestError as e:
        return error_response("network_error", str(e), 503)
    except Exception as e:
        return error_response("video_create_error", str(e), 500)


# ==========================================================
# 🔁 Remix Video
# ==========================================================
@router.post("/{video_id}/remix")
async def remix_video(video_id: str, request: Request):
    """
    Remix an existing video with a new prompt.
    """
    try:
        body = await request.json()
        prompt = body.get("prompt", "Remix this video")
        payload = {"prompt": prompt}

        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.post(
                f"{OPENAI_BASE_URL}/v1/videos/{video_id}/remix",
                headers={**_headers(), "Content-Type": "application/json"},
                json=payload,
            )

        return Response(
            content=resp.text,
            media_type=resp.headers.get("content-type", "application/json"),
            status_code=resp.status_code,
        )

    except Exception as e:
        return error_response("video_remix_error", str(e), 500)


# ==========================================================
# 🧠 Retrieve Metadata
# ==========================================================
@router.get("/{video_id}")
async def get_video_metadata(video_id: str):
    """
    Get metadata or render progress for a Sora 2 Pro video.
    """
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.get(
                f"{OPENAI_BASE_URL}/v1/videos/{video_id}",
                headers=_headers(),
            )

        return Response(
            content=resp.text,
            media_type=resp.headers.get("content-type", "application/json"),
            status_code=resp.status_code,
        )

    except Exception as e:
        return error_response("video_metadata_error", str(e), 500)


# ==========================================================
# 📦 Download Content
# ==========================================================
@router.get("/{video_id}/content")
async def download_video(video_id: str):
    """
    Stream the MP4 for a completed Sora 2 Pro render.
    """
    try:
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream(
                "GET",
                f"{OPENAI_BASE_URL}/v1/videos/{video_id}/content",
                headers=_headers(),
            ) as upstream:
                return Response(
                    content=upstream.aiter_bytes(),
                    status_code=upstream.status_code,
                    media_type="video/mp4",
                )

    except Exception as e:
        return error_response("video_content_error", str(e), 500)
