# app/routes/responses.py

from __future__ import annotations

from typing import Any, AsyncIterator, Dict

from fastapi import APIRouter, Body
from fastapi.responses import JSONResponse, StreamingResponse

from app.api.forward_openai import (
    forward_responses_create,
    forward_responses_create_streaming,
    forward_responses_compact,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/v1",
    tags=["responses"],
)


# ---------------------------------------------------------------------------
# SSE helpers
# ---------------------------------------------------------------------------


async def _iter_sse_events(stream: Any) -> AsyncIterator[bytes]:
    """
    Transform the Responses API's streaming event iterator into
    server-sent events (SSE) bytes for the HTTP client.
    """
    async for event in stream:
        # Each 'event' is an OpenAI response event object.
        # We translate it into SSE format: "event: <type>\\ndata: <json>\\n\\n"
        event_type = getattr(event, "type", "message")
        payload = (
            event.model_dump()
            if hasattr(event, "model_dump")
            else event
        )

        # JSONResponse handles JSON encoding and ensures unicode escapes, etc.
        json_bytes = JSONResponse(content=payload).body
        json_text = json_bytes.decode("utf-8")

        yield (
            f"event: {event_type}\n"
            f"data: {json_text}\n\n"
        ).encode("utf-8")


# ---------------------------------------------------------------------------
# /v1/responses – main Responses API entrypoint
# ---------------------------------------------------------------------------


@router.post("/responses")
async def create_response(
    body: Dict[str, Any] = Body(
        ...,
        description="OpenAI Responses API payload",
    ),
) -> StreamingResponse | JSONResponse:
    """
    Proxy for OpenAI's /v1/responses endpoint.

    If the request includes `"stream": true`, the call is forwarded using the
    typed SDK streaming interface and we expose it to the client as a
    Server-Sent Events (SSE) stream.

    Otherwise this behaves like a normal JSON POST and returns the full
    response object when it completes.
    """
    stream_flag = bool(body.get("stream"))
    logger.info("Incoming /v1/responses request (stream=%s)", stream_flag)

    if stream_flag:
        # Typed streaming via SDK: returns an async iterator of events which
        # we wrap into SSE bytes.
        stream = forward_responses_create_streaming(body)
        return StreamingResponse(
            _iter_sse_events(stream),
            media_type="text/event-stream",
        )

    # Non-streaming: forward and return JSON.
    result = await forward_responses_create(body)
    return JSONResponse(content=result)


# ---------------------------------------------------------------------------
# /v1/responses/compact – Responses.compact endpoint
# ---------------------------------------------------------------------------


@router.post("/responses/compact")
async def compact_response(
    body: Dict[str, Any] = Body(
        ...,
        description=(
            "OpenAI Responses.compact payload. Mirrors the body of "
            "POST /v1/responses, but runs a compaction pass over the "
            "conversation instead of generating fresh output."
        ),
    ),
) -> JSONResponse:
    """
    Proxy for OpenAI's /v1/responses/compact endpoint.

    This endpoint runs a **compaction** pass over a long-running conversation
    and returns a compacted response object that you can feed back into future
    /v1/responses calls (via `previous_response_id`) to avoid resending the
    entire history. :contentReference[oaicite:4]{index=4}
    """
    logger.info("Incoming /v1/responses/compact request")
    result = await forward_responses_compact(body)
    return JSONResponse(content=result)
