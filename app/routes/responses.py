# app/routes/responses.py

from __future__ import annotations

import json
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


async def _iter_sse_events(stream: Any) -> AsyncIterator[bytes]:
    """
    Turn an OpenAI AsyncStream of Response events into Server-Sent Events (SSE).

    Each event is sent as:

        event: <event.type>
        data: <json-encoded event>

    followed by a blank line, per SSE spec.
    """
    async for event in stream:
        try:
            event_type = getattr(event, "type", None)

            if hasattr(event, "model_dump_json"):
                # Pydantic v2 models from the OpenAI SDK
                data_json = event.model_dump_json(exclude_none=True)
            elif hasattr(event, "model_dump"):
                data_json = json.dumps(event.model_dump(exclude_none=True))
            elif isinstance(event, dict):
                data_json = json.dumps(event)
            else:
                # Very defensive fallback – shouldn't normally happen
                data_json = json.dumps({"data": str(event)})

            if event_type:
                chunk = f"event: {event_type}\ndata: {data_json}\n\n"
            else:
                chunk = f"data: {data_json}\n\n"

        except Exception as exc:  # pragma: no cover - ultra defensive
            # If serialization of a single event fails, send an error event
            error_payload = json.dumps(
                {
                    "type": "response.error",
                    "error": {
                        "message": f"Failed to serialize streaming event: {exc}",
                        "code": "relay_sse_serialization_error",
                    },
                }
            )
            chunk = f"event: response.error\ndata: {error_payload}\n\n"

        yield chunk.encode("utf-8")


@router.post("/responses")
async def create_response(
    body: Dict[str, Any] = Body(..., description="OpenAI Responses.create payload"),
) -> Any:
    """
    Proxy for OpenAI Responses API.

    Mirrors:
        POST https://api.openai.com/v1/responses

    Behavior:
      - If `stream` is falsy or absent, behaves like a normal JSON proxy and
        returns the upstream OpenAI response as JSON.
      - If `stream` is truthy, uses SSE (`text/event-stream`) and forwards the
        OpenAI AsyncStream as a Server‑Sent Event stream.
    """
    logger.info("Incoming /v1/responses request")

    stream_param = body.get("stream")

    # Treat `stream: true` or any truthy value / object as a streaming request
    if stream_param:
        logger.info("Handling /v1/responses as streaming SSE request")
        # This will return an openai.AsyncStream when `stream` is truthy
        upstream_stream = await forward_responses_create(body)

        return StreamingResponse(
            _iter_sse_events(upstream_stream),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                # Helps disable buffering on some proxies (e.g. nginx)
                "X-Accel-Buffering": "no",
            },
        )

    # Non-streaming: just proxy through and let FastAPI serialize the JSON
    logger.info("Handling /v1/responses as non-streaming JSON request")
    return await forward_responses_create(body)
