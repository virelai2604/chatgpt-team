# app/routes/responses.py

from __future__ import annotations

from typing import Any, AsyncIterator, Dict

from fastapi import APIRouter, Body
from fastapi.responses import StreamingResponse

from app.api.forward_openai import forward_responses_create
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/v1",
    tags=["responses"],
)


async def _events_to_sse(openai_stream) -> AsyncIterator[str]:
    """
    Bridge OpenAI's AsyncStream[ResponseStreamEvent] into Server-Sent Events.

    For each event from the OpenAI SDK, we emit an SSE frame that mirrors
    the upstream Responses API streaming format:

        event: <event.type>
        data: <json>\n\n
    """
    import json

    async for event in openai_stream:
        # Determine the event type (e.g. "response.created", "response.completed", etc.)
        event_type = getattr(event, "type", "message")

        # Serialize the event payload to JSON in a robust way
        try:
            if hasattr(event, "model_dump_json"):
                payload = event.model_dump_json()
            elif hasattr(event, "json"):
                payload = event.json()
            elif hasattr(event, "model_dump"):
                payload = json.dumps(event.model_dump())
            else:
                payload = json.dumps(event)
        except Exception:
            # Defensive fallback, so a weird event doesn't kill the stream
            payload = json.dumps({"error": "failed_to_serialize_event"})

        # Standard SSE frame: "event" line, "data" line, then a blank line
        yield f"event: {event_type}\n"
        yield f"data: {payload}\n\n"


@router.post("/responses")
async def create_response(
    body: Dict[str, Any] = Body(
        ...,
        description="OpenAI Responses.create payload",
    ),
) -> Any:
    """
    Proxy for OpenAI Responses API.

    Mirrors:
        POST https://api.openai.com/v1/responses

    Behavior:
      - If `stream` is falsy or omitted: simple JSON response (non-streaming).
      - If `stream` is true: text/event-stream SSE, mirroring api.openai.com.
    """
    logger.info("Incoming /v1/responses request")

    stream = bool(body.get("stream"))

    # Non-streaming: return the full JSON response
    if not stream:
        logger.info("Handling /v1/responses as non-streaming JSON request")
        return await forward_responses_create(body)

    # Streaming: turn the OpenAI AsyncStream into SSE frames
    logger.info("Handling /v1/responses as streaming SSE request")

    # The forwarder should call OpenAI with streaming enabled and return
    # an AsyncStream[ResponseStreamEvent]-like object.
    openai_stream = await forward_responses_create(body)

    return StreamingResponse(
        _events_to_sse(openai_stream),
        media_type="text/event-stream",
    )
