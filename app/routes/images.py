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
`forward_openai_request`, so the relay automatically tracks changes in
the upstream API and openai-python SDK.
"""

from __future__ import annotations

from fastapi import APIRouter, Request

from app.api.forward_openai import forward_openai_request
from app.utils.logger import relay_log as logger
from app.utils.auth import verify_relay_key


router = APIRouter(
    prefix="/v1",
    tags=["images"],
    dependencies=[verify_relay_key],
)


@router.post("/images")
async def create_images_root(request: Request):
    """
    POST /v1/images

    "Best-effort" proxy for image generation. This exists primarily to
    support older clients and tests (e.g. relay_e2e_raw.py) that POST
    directly to `/v1/images` instead of `/v1/images/generations`.

    The body is forwarded 1:1 to the upstream Images API. If the upstream
    endpoint does not support this path, the OpenAI error is returned
    unchanged to the client.
    """
    logger.info("→ [images] %s %s (root)", request.method, request.url.path)
    return await forward_openai_request(request)


@router.post("/images/generations")
async def create_image_generations(request: Request):
    """
    POST /v1/images/generations

    Generates one or more images from a text prompt, equivalent to:

        client.images.generate({
          "model": "gpt-image-1",
          "prompt": "...",
          ...
        })

    The request body and response payload are forwarded 1:1 to/from
    the upstream OpenAI Images API by `forward_openai_request`.
    """
    logger.info("→ [images] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.api_route("/images/{path:path}", methods=["GET", "POST", "DELETE", "HEAD", "OPTIONS"])
async def proxy_images_subpaths(path: str, request: Request):
    """
    /v1/images/{...} — catch-all for image sub-resources.

    This route covers any additional or legacy endpoints under
    /v1/images/*, such as:

      • POST /v1/images/edits
      • POST /v1/images/variations
      • Any future subpaths introduced by OpenAI.

    We simply forward the HTTP method, path, headers, and body to
    the upstream API via `forward_openai_request`.
    """
    logger.info(
        "→ [images] %s %s (subpath=%s)",
        request.method,
        request.url.path,
        path,
    )
    return await forward_openai_request(request)
