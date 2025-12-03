# app/routes/images.py

"""
images.py — /v1/images proxy
─────────────────────────────
Thin, OpenAI-compatible proxy for image generation (and related
image operations) via the official Images API.
"""

from __future__ import annotations

from fastapi import APIRouter, Request, Response

from app.api.forward_openai import forward_openai_request
from app.utils.logger import relay_log as logger

router = APIRouter(
    prefix="/v1",
    tags=["images"],
)


@router.post("/images")
async def create_images_root(request: Request) -> Response:
    """
    Convenience entrypoint for clients that POST /v1/images directly.
    """
    logger.info("→ [images] POST %s", request.url.path)
    return await forward_openai_request(request)


@router.post("/images/generations")
async def create_image_generations(request: Request) -> Response:
    """
    POST /v1/images/generations – main image generation endpoint.
    """
    logger.info("→ [images] POST %s", request.url.path)
    return await forward_openai_request(request)


@router.api_route(
    "/images/{path:path}",
    methods=["GET", "POST", "DELETE", "HEAD", "OPTIONS"],
)
async def proxy_images_subpaths(path: str, request: Request) -> Response:
    """
    Catch-all for /v1/images/*, including:

      - /v1/images/edits
      - /v1/images/variations
      - any future image-related subroutes
    """
    logger.info("→ [images/*] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)
