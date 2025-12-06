# app/api/sse.py

from __future__ import annotations

from typing import AsyncIterator, Dict, Any

from fastapi import APIRouter, Body
from fastapi.responses import StreamingResponse

from app.core.http_client import get_async_openai_client
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["responses-stream"])


async def _responses_event_stream(payload: Dict[str, Any]) -> AsyncIterator[bytes]:
    """
    Stream Responses API events as SSE (Server-Sent Events).

    The client-side can consume this exactly like a normal OpenAI stream.
    """
    client = get_async_openai_client()
    stream = await client.responses.create(**payload, stream=True)
    async for event in stream:
        # The OpenAI SDK yields typed events; we just serialize them.
        data = event.model_dump_json()
        yield f"data: {data}\n\n".encode("utf-8")


@router.post("/v1/responses:stream")
async def responses_stream(
    payload: Dict[str, Any] = Body(...),
) -> StreamingResponse:
    """
    SSE-compatible streaming endpoint for Responses API.

    Mirrors POST /v1/responses with stream semantics.
    """
    logger.debug("Starting Responses stream request")
    return StreamingResponse(
        _responses_event_stream(payload),
        media_type="text/event-stream",
    )
