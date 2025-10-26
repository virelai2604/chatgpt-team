# ==========================================================
# app/routes/images.py — BIFL v2.3.4-fp
# ==========================================================
# Unified OpenAI-compatible image endpoint layer.
#   /v1/images/generations
#   /v1/images/edits
#   /v1/images/variations
# Handles base64 decoding and optional streaming.
# ==========================================================

import base64, io
from fastapi import APIRouter, Request, Response
from app.api.forward import forward_openai

router = APIRouter(prefix="/v1/images", tags=["Images"])

# ----------------------------------------------------------
# 🖼️  Image Generation
# ----------------------------------------------------------
@router.post("/generations")
async def create_image(request: Request):
    """
    Forward an image generation request to OpenAI.
    Example:
      {
        "model": "gpt-image-1",
        "prompt": "A cyberpunk cityscape at sunset",
        "size": "1024x1024",
        "stream": true
      }
    """
    return await forward_openai(request, "/v1/images/generations")

# ----------------------------------------------------------
# ✂️  Image Editing
# ----------------------------------------------------------
@router.post("/edits")
async def edit_image(request: Request):
    """
    Forward an image editing request.
    Accepts multipart form (image + mask) or JSON.
    """
    return await forward_openai(request, "/v1/images/edits")

# ----------------------------------------------------------
# 🔁  Image Variations
# ----------------------------------------------------------
@router.post("/variations")
async def image_variation(request: Request):
    """Forward image variation request."""
    return await forward_openai(request, "/v1/images/variations")

# ----------------------------------------------------------
# 🧩  Local Base64 Decode Helper (optional)
# ----------------------------------------------------------
@router.post("/decode")
async def decode_base64_image(request: Request):
    """
    Optional local utility to decode base64 → binary bytes.
    Not an OpenAI endpoint; for debugging client output.
    """
    body = await request.json()
    b64 = body.get("data")
    if not b64:
        return Response(
            content='{"error":"missing base64 data"}',
            media_type="application/json",
            status_code=400,
        )
    try:
        binary_data = base64.b64decode(b64)
        return Response(
            content=binary_data,
            media_type="image/png",
            status_code=200,
        )
    except Exception as e:
        return Response(
            content=f'{{"error":"{e}"}}',
            media_type="application/json",
            status_code=400,
        )
