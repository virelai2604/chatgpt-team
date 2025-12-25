from __future__ import annotations

import asyncio
from typing import Optional

from fastapi import APIRouter, Request
from fastapi.responses import Response

from app.api.forward_openai import forward_openai_request

router = APIRouter(prefix="/v1", tags=["uploads"])


async def _forward_with_transient_retry(
    request: Request,
    *,
    max_retries: int = 2,
    base_delay_s: float = 0.25,
) -> Response:
    """
    Best-effort mitigation for occasional upstream 5xx from OpenAI.
    This is especially useful for integration gates that exercise /v1/uploads.

    - Retries only on 5xx
    - Exponential backoff: base_delay * 2^attempt
    """
    resp: Response = await forward_openai_request(request)
    attempt = 0

    while attempt < max_retries and getattr(resp, "status_code", 200) >= 500:
        await asyncio.sleep(base_delay_s * (2**attempt))
        resp = await forward_openai_request(request)
        attempt += 1

    return resp


@router.post("/uploads")
async def create_upload(request: Request) -> Response:
    return await _forward_with_transient_retry(request)


@router.post("/uploads/{upload_id}/parts")
async def create_upload_part(request: Request, upload_id: str) -> Response:
    return await forward_openai_request(request)


@router.post("/uploads/{upload_id}/complete")
async def complete_upload(request: Request, upload_id: str) -> Response:
    return await forward_openai_request(request)


@router.post("/uploads/{upload_id}/cancel")
async def cancel_upload(request: Request, upload_id: str) -> Response:
    return await forward_openai_request(request)
