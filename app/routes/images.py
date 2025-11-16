"""
images.py — /v1/images
───────────────────────
Thin proxy for OpenAI Images API (DALL·E / gpt-image-*).

The official API uses:
  POST /v1/images with multipart/form-data or JSON body
  depending on the SDK. Here we support form uploads for
  maximum compatibility; JSON-only callers can fall back
  through P4 passthrough if needed.
"""

import os
import httpx
from fastapi import APIRouter, Request, UploadFile, File, Form
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/v1", tags=["images"])

OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TIMEOUT = float(os.getenv("RELAY_TIMEOUT", "120"))


def _headers():
    return {"Authorization": f"Bearer {OPENAI_API_KEY}"}


@router.post("/images")
async def create_image(
    prompt: str = Form(...),
    model: str = Form("gpt-image-1"),
    size: str = Form("1024x1024"),
    n: int = Form(1),
):
    """
    Basic wrapper for POST /v1/images with form fields.

    For more advanced options (JSON bodies, masks, etc.) clients
    can hit /v1/images directly via P4Orchestrator passthrough.
    """
    data = {
        "model": model,
        "prompt": prompt,
        "size": size,
        "n": n,
    }

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.post(
            f"{OPENAI_API_BASE.rstrip('/')}/images",
            headers={**_headers(), "Content-Type": "application/json"},
            json=data,
        )
        return JSONResponse(resp.json(), status_code=resp.status_code)
