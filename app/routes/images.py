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
      - POST /v1/images

    Tests:
      - test_image_generations_forward

    They assert:
      * HTTP 200
      * JSON body matches the stub from `forward_spy`
        (echo_path == "/v1/images/generations", echo_method == "POST")
    """
    logger.info("→ [images] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.post("/images/edits")
async def edit_image(request: Request) -> Response:
    """
    Image edits passthrough.

    The test stubs the upstream endpoint:
      POST https://api.openai.com/v1/images/edits

    Our job is simply to forward the request and return whatever
    upstream sends (status code + JSON body).
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
      - Upstream expects multipart/form-data with an 'image' file field.
      - Typically used with DALL·E 2 class models (depending on OpenAI support).
    """
    logger.info("→ [images] %s %s (variations)", request.method, request.url.path)
    return await forward_openai_request(request)
