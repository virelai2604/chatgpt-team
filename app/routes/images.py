# app/routes/images.py

from __future__ import annotations

from fastapi import APIRouter, Request, Response

from app.api.forward_openai import forward_openai_request
from app.utils.logger import relay_log as logger

router = APIRouter(
    prefix="/v1",
    tags=["images"],
)


@router.post("/images/generations")
@router.post("/images")
async def create_image(request: Request) -> Response:
    """
    Image generation passthrough.

    Covers:
      - POST /v1/images/generations
      - POST /v1/images (alias)

    Notes:
      - Typical payload is JSON.
    """
    logger.info("→ [images] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.post("/images/edits")
async def edit_image(request: Request) -> Response:
    """
    Image edits passthrough.

    Covers:
      - POST /v1/images/edits

    Notes:
      - Commonly multipart/form-data (file upload). We forward as-is.
    """
    logger.info("→ [images] %s %s (edits)", request.method, request.url.path)
    return await forward_openai_request(request)


@router.post("/images/variations")
async def create_image_variation(request: Request) -> Response:
    """
    Image variations passthrough.

    Covers:
      - POST /v1/images/variations

    Notes:
      - Commonly multipart/form-data (image file input). We forward as-is.
    """
    logger.info("→ [images] %s %s (variations)", request.method, request.url.path)
    return await forward_openai_request(request)
