# app/routes/images.py

"""
images.py — /v1/images proxy
─────────────────────────────
Thin, OpenAI-compatible proxy for image generation and related
image operations via the official Images API.

Main endpoints (per current OpenAI docs):

  • POST /v1/images/generations   → generate images from a prompt
  • POST /v1/images/edits         → edit existing images
  • POST /v1/images/variations    → generate variations

Legacy / extended endpoints MAY include:

  • POST /v1/images               → "best-effort" entrypoint some clients call

This router intentionally does NOT encode any business logic or
parameter validation. All behavior is delegated to
`forward_openai_request`, so the relay automatically tracks
changes in the upstream API and openai-python SDK.
"""

from __future__ import annotations

from fastapi import APIRouter, Request, Response

from app.api.forward_openai import forward_openai_request
from app.utils.logger import relay_log as logger

router = APIRouter(
    prefix="/v1",
    tags=["images"],
    # Auth is handled centrally by RelayAuthMiddleware.
)


@router.post("/images")
async def create_images_root(request: Request) -> Response:
    """
    POST /v1/images

    Convenience/legacy entrypoint for clients that call /v1/images directly.
    Proxies to OpenAI Images API without modification.
    """
    logger.debug("Proxying POST /v1/images")
    return await forward_openai_request(request)


@router.post("/images/generations")
async def create_image_generations(request: Request) -> Response:
    """
    POST /v1/images/generations

    Primary image generation endpoint.
    """
    logger.debug("Proxying POST /v1/images/generations")
    return await forward_openai_request(request)


@router.post("/images/edits")
async def create_image_edits(request: Request) -> Response:
    """
    POST /v1/images/edits

    Image editing endpoint.
    """
    logger.debug("Proxying POST /v1/images/edits")
    return await forward_openai_request(request)


@router.post("/images/variations")
async def create_image_variations(request: Request) -> Response:
    """
    POST /v1/images/variations

    Generate variations of an existing image.
    """
    logger.debug("Proxying POST /v1/images/variations")
    return await forward_openai_request(request)


@router.api_route(
    "/images/{path:path}",
    methods=["GET", "POST", "DELETE", "HEAD", "OPTIONS"],
)
async def proxy_images_subpaths(path: str, request: Request) -> Response:
    """
    Generic catch-all proxy for any future /v1/images/* subpaths.

    This ensures the relay remains compatible with new image-related routes
    without requiring code changes, while still passing through full
    request/response bodies.
    """
    logger.debug("Proxying /v1/images/%s with method %s", path, request.method)
    return await forward_openai_request(request)
