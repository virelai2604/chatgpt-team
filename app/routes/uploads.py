# app/routes/uploads.py

from __future__ import annotations

from fastapi import APIRouter, Request, Response

from app.api.forward_openai import forward_openai_request
from app.utils.logger import relay_log as logger

router = APIRouter(prefix="/v1", tags=["uploads"])


@router.post("/uploads")
async def create_upload(request: Request) -> Response:
    """
    POST /v1/uploads
    Passthrough to upstream.
    """
    return await forward_openai_request(request)


@router.api_route(
    "/uploads/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"],
    include_in_schema=False,
)
async def uploads_passthrough(path: str, request: Request) -> Response:
    """
    Catch-all passthrough for future /v1/uploads/* endpoints.
    Kept out of OpenAPI to avoid duplicate operationId noise.
    """
    logger.info("→ [uploads/*] %s %s (subpath=%s)", request.method, request.url.path, path)
    return await forward_openai_request(request)
