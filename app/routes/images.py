"""
images.py — /v1/images
───────────────────────
Thin proxy for OpenAI Images API (gpt-image-*).

The official API uses:
  POST /v1/images with JSON body in the current SDKs.

Here we expose a simple form-based wrapper that constructs the JSON
for you. More advanced callers can hit /v1/images directly via the
P4Orchestrator passthrough.
"""

import os

import httpx
from fastapi import APIRouter, Form
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/v1", tags=["images"])

OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_ORG_ID = os.getenv("OPENAI_ORG_ID", "")
TIMEOUT = float(os.getenv("RELAY_TIMEOUT", "120"))


def _headers() -> dict:
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    if OPENAI_ORG_ID:
        headers["OpenAI-Organization"] = OPENAI_ORG_ID
    return headers


def _images_url() -> str:
    return f"{OPENAI_API_BASE.rstrip('/')}/v1/images"


@router.post("/images")
async def create_image(
    prompt: str = Form(...),
    model: str = Form("gpt-image-1"),
    size: str = Form("1024x1024"),
    n: int = Form(1),
):
    """
    Basic wrapper for POST /v1/images with form fields.

    Equivalent to:
      client.images.generate({
        "model": "gpt-image-1",
        "prompt": "...",
        "size": "1024x1024",
        "n": 1
      })
    """
    data = {
        "model": model,
        "prompt": prompt,
        "size": size,
        "n": n,
    }

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.post(
            _images_url(),
            headers=_headers(),
            json=data,
        )
        return JSONResponse(resp.json(), status_code=resp.status_code)
