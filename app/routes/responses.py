from __future__ import annotations

import json
from typing import Any, AsyncGenerator, Dict

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, Response as FastAPIResponse, StreamingResponse
from starlette.requests import ClientDisconnect

from app.api.forward_openai import build_upstream_url, forward_openai_request, forward_responses_create
from app.core.config import settings
from app.core.http_client import get_async_httpx_client
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/v1/responses")
async def create_response(request: Request) -> Any:
    try:
        body: Dict[str, Any] = await request.json()
    except ClientDisconnect:
        return FastAPIResponse(status_code=499)

    stream = bool(body.get("stream"))

    if not stream:
        logger.info("Handling /v1/responses as non-streaming JSON request")
        resp = await forward_responses_create(body)
        # openai-python returns pydantic models with model_dump()
        return JSONResponse(content=resp.model_dump() if hasattr(resp, "model_dump") else resp)

    logger.info("Handling /v1/responses as streaming SSE request (raw pass-through)")

    upstream_url = build_upstream_url("/v1/responses")

    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
    }

    client = get_async_httpx_client()

    # Open upstream stream *now* so we can propagate status_code correctly.
    upstream_cm = client.stream(
        "POST",
        upstream_url,
        headers=headers,
        content=json.dumps(body).encode("utf-8"),
    )
    upstream = await upstream_cm.__aenter__()

    if upstream.status_code >= 400:
        err = await upstream.aread()
        await upstream_cm.__aexit__(None, None, None)
        return FastAPIResponse(
            content=err,
            status_code=upstream.status_code,
            media_type=upstream.headers.get("content-type", "application/json"),
        )

    async def sse_passthrough() -> AsyncGenerator[bytes, None]:
        try:
            async for chunk in upstream.aiter_raw():
                yield chunk
        finally:
            await upstream_cm.__aexit__(None, None, None)

    resp_headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }
    return StreamingResponse(
        sse_passthrough(),
        status_code=upstream.status_code,
        media_type="text/event-stream",
        headers=resp_headers,
    )


@router.post("/v1/responses/compact")
async def compact_response(request: Request) -> Any:
    """
    OpenAI supports POST /v1/responses/compact (model required). 
    We forward it generically to upstream so your relay stays future-proof.
    """
    logger.info("Incoming /v1/responses/compact request")
    return await forward_openai_request(request)
