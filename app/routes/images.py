"""
images.py — /v1/images & /v1/images/generations
───────────────────────────────────────────────
Thin proxy for the OpenAI Images API (gpt-image-*).

Ground truth (API Reference):
  • Generate images: POST /v1/images/generations
    Body: { "model": "gpt-image-1", "prompt": "...", "n": 1, "size": "1024x1024", ... }
    See: https://api.openai.com/v1/images/generations
"""

import os
from typing import Any, Dict

import httpx
from fastapi import APIRouter, Body, Form, Request
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/v1", tags=["images"])

OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_ORG_ID = os.getenv("OPENAI_ORG_ID", "")
TIMEOUT = float(os.getenv("RELAY_TIMEOUT", "120"))


def _headers() -> Dict[str, str]:
    """
    Standard JSON headers for calling OpenAI's Images API.
    """
    headers: Dict[str, str] = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    if OPENAI_ORG_ID:
        headers["OpenAI-Organization"] = OPENAI_ORG_ID
    return headers


def _images_generations_url() -> str:
    """
    Official upstream endpoint:
      POST https://api.openai.com/v1/images/generations
    """
    return f"{OPENAI_API_BASE.rstrip('/')}/v1/images/generations"


@router.post("/images")
async def create_image_form(
    prompt: str = Form(...),
    model: str = Form("gpt-image-1"),
    size: str = Form("1024x1024"),
    n: int = Form(1),
):
    """
    Convenience wrapper for image generation using HTML form fields.

    Effectively equivalent to:

        client.images.generate(
            model="gpt-image-1",
            prompt="...",
            size="1024x1024",
            n=1,
        )

    but exposed as:
        POST /v1/images  (form-data)
    and forwarded as JSON to the official upstream:
        POST /v1/images/generations
    """
    data: Dict[str, Any] = {
        "model": model,
        "prompt": prompt,
        "size": size,
        "n": n,
    }

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.post(
            _images_generations_url(),
            headers=_headers(),
            json=data,
        )

    return JSONResponse(resp.json(), status_code=resp.status_code)


@router.post("/images/generations")
async def create_image_generation(
    request: Request,
    body: Dict[str, Any] = Body(...),
):
    """
    JSON-compatible proxy for the official Images Generations endpoint.

    Matches the API reference:

        POST https://api.openai.com/v1/images/generations
        Body:
        {
          "model": "gpt-image-1",
          "prompt": "A cute baby sea otter",
          "n": 1,
          "size": "1024x1024",
          ...
        }

    Used by:
        • tests/test_embeddings_images_videos.py::test_images_generation
        • openai-python client.images.generate(...)
    """
    # Ensure we have a body even if someone sends raw JSON without using `body` param
    if not body:
        try:
            body = await request.json()
        except Exception:
            body = {}

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.post(
            _images_generations_url(),
            headers=_headers(),
            json=body,
        )

    return JSONResponse(resp.json(), status_code=resp.status_code)
