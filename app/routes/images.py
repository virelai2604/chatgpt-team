"""
images.py — /v1/images proxy
─────────────────────────────
Thin, OpenAI-compatible proxy for image generation (and any related
image operations) via the official Images API.

Main endpoint (per current OpenAI docs):

  • POST /v1/images/generations   → generate images from a prompt

Legacy / extended endpoints MAY include:

  • POST /v1/images               → "best-effort" entrypoint some clients call
  • POST /v1/images/edits         → edit existing images
  • POST /v1/images/variations    → generate variations

This router intentionally does NOT encode any business logic or
parameter validation. All behavior is delegated to
`forward_openai_request`, so the relay automatically tracks
changes in the upstream API and openai-python SDK.
"""

from __future__ import annotations

from fastapi import APIRouter, Request

from app.api.forward_openai import forward_openai_request
from app.utils.logger import relay_log as logger

router = APIRouter(
    prefix="/v1",
    tags=["images"],
    # Auth is handled centrally by RelayAuthMiddleware.
)


@router.post("/images")
async def create_images_root(request: Request):
    ...
    return await forward_openai_request(request)


@router.post("/images/generations")
async def create_image_generations(request: Request):
    ...
    return await forward_openai_request(request)


@router.api_route("/images/{path:path}", methods=["GET", "POST", "DELETE", "HEAD", "OPTIONS"])
async def proxy_images_subpaths(path: str, request: Request):
    ...
    return await forward_openai_request(request)
