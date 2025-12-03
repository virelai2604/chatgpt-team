# app/routes/images.py
"""
images.py — /v1/images proxy

Thin, OpenAI-compatible proxy for image generation and related operations.

Main endpoints (per current docs):
  • POST /v1/images/generations  → generate images from a prompt

Extended / legacy endpoints (supported via catch-all):
  • POST /v1/images/edits
  • POST /v1/images/variations
  • any future /v1/images/* paths

All behavior is delegated to `forward_openai_request`, which handles
JSON vs stream, headers, and error envelopes.
"""

from __future__ import annotations

from fastapi import APIRouter, Request, Response

from app.api.forward_openai import forward_openai_request
from app.utils.logger import relay_log as logger

router = APIRouter(
    prefix="/v1",
    tags=["images"],
)


@router.api_route("/images", methods=["POST", "HEAD", "OPTIONS"])
async def create_images_root(request: Request) -> Response:
    """
    Entry point for clients that call POST /v1/images directly.
    """
    logger.info("→ [images] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.post("/images/generations")
async def create_image_generations(request: Request) -> Response:
    """
    Canonical Images API (per OpenAI API Reference).
    """
    logger.info("→ [images/generations] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.api_route(
    "/images/{path:path}",
    methods=["GET", "POST", "DELETE", "HEAD", "OPTIONS"],
)
async def proxy_images_subpaths(path: str, request: Request) -> Response:
    """
    Catch-all for all image-related paths.

    Examples:
      - POST /v1/images/edits
      - POST /v1/images/variations
      - any new /v1/images/* paths added by OpenAI in the future
    """
    logger.info("→ [images/*] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)
