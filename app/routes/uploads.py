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

    Upstream: Creates an intermediate Upload; once completed, it yields a File.
    (OpenAI API Reference: Uploads)
    """
    logger.info("→ [uploads] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.post("/uploads/{upload_id}/parts")
async def add_upload_part(upload_id: str, request: Request) -> Response:
    """
    POST /v1/uploads/{upload_id}/parts

    Upstream expects multipart/form-data with a required 'data' file field.
    We forward as-is.
    """
    logger.info("→ [uploads] %s %s (upload_id=%s)", request.method, request.url.path, upload_id)
    return await forward_openai_request(request)


@router.post("/uploads/{upload_id}/complete")
async def complete_upload(upload_id: str, request: Request) -> Response:
    """
    POST /v1/uploads/{upload_id}/complete

    Upstream expects JSON body:
      {"part_ids": ["part_...","part_..."], "md5": "..."}  # md5 optional
    """
    logger.info("→ [uploads] %s %s (complete upload_id=%s)", request.method, request.url.path, upload_id)
    return await forward_openai_request(request)


@router.post("/uploads/{upload_id}/cancel")
async def cancel_upload(upload_id: str, request: Request) -> Response:
    """
    POST /v1/uploads/{upload_id}/cancel
    """
    logger.info("→ [uploads] %s %s (cancel upload_id=%s)", request.method, request.url.path, upload_id)
    return await forward_openai_request(request)


@router.api_route(
    "/uploads/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"],
    include_in_schema=False,
)
async def uploads_passthrough(path: str, request: Request) -> Response:
    """
    Catch-all passthrough for future /v1/uploads/* endpoints.
    """
    logger.info("→ [uploads/*] %s %s (subpath=%s)", request.method, request.url.path, path)
    return await forward_openai_request(request)
