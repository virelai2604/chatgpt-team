from __future__ import annotations

import asyncio

from fastapi import APIRouter, Request
from fastapi.responses import Response

from app.api.forward_openai import forward_openai_request
from app.utils.logger import relay_log as logger

router = APIRouter(prefix="/v1", tags=["uploads"])


@router.post("/uploads", summary="Create upload")
async def create_upload(request: Request) -> Response:
    logger.info("→ [uploads] POST %s", request.url.path)
    return await forward_openai_request(request)


@router.get("/uploads/{upload_id}", summary="Get upload")
async def get_upload(upload_id: str, request: Request) -> Response:
    logger.info("→ [uploads] GET %s", request.url.path)
    return await forward_openai_request(request)


@router.post("/uploads/{upload_id}/parts", summary="Add upload part")
async def add_upload_part(upload_id: str, request: Request) -> Response:
    logger.info("→ [uploads] POST %s", request.url.path)
    return await forward_openai_request(request)


@router.post("/uploads/{upload_id}/complete", summary="Complete upload")
async def complete_upload(upload_id: str, request: Request) -> Response:
    """
    Complete an upload. The upstream endpoint has occasionally returned transient 5xx errors
    immediately after parts are uploaded. We apply a small retry/backoff to improve reliability.
    """
    logger.info("→ [uploads] POST %s", request.url.path)

    resp = await forward_openai_request(request)

    # Retry only on 5xx.
    if resp.status_code >= 500:
        for delay in (0.25, 0.75):
            await asyncio.sleep(delay)
            logger.info("↻ [uploads] retry complete after %.2fs", delay)
            resp = await forward_openai_request(request)
            if resp.status_code < 500:
                break

    return resp


@router.post("/uploads/{upload_id}/cancel", summary="Cancel upload")
async def cancel_upload(upload_id: str, request: Request) -> Response:
    logger.info("→ [uploads] POST %s", request.url.path)
    return await forward_openai_request(request)


# Passthrough for any future /uploads subroutes not explicitly defined above.
@router.api_route(
    "/uploads/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    include_in_schema=False,
)
async def uploads_passthrough(path: str, request: Request) -> Response:
    logger.info("→ [uploads] passthrough %s %s", request.method, request.url.path)
    return await forward_openai_request(request)
