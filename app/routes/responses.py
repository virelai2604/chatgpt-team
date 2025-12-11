# app/routes/responses.py

from __future__ import annotations

import asyncio
import json
from typing import Any, AsyncIterator, Dict

from fastapi import APIRouter, Body, Request
from fastapi.responses import StreamingResponse

from app.api.forward_openai import forward_responses_create
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/v1", tags=["openai-responses"])


async def _iter_sse_events(stream: Any) -> AsyncIterator[bytes]:
    """
    Bridge an openai.AsyncStream[ResponseStreamEvent] to Server‑Sent Events.

    We:
    - async-iterate over `stream`
    - call `event.model_dump_json()` when available, or `json.dumps(event)`
    - wrap as `data: <json>\\n\\n`
    - finally emit `data: [DONE]\\n\\n`
    """
    try:
        async for event in stream:
            # Newer openai-python ResponseStreamEvent has model_dump_json()
            if hasattr(event, "model_dump_json"):
                payload = event.model_dump_json()
            else:
                # Fallback, just in case
                try:
                    payload = json.dumps(event)
                except TypeError:
                    payload = json.dumps({"type": getattr(event, "type", "unknown")})

            text = f"data: {payload}\n\n"
            yield text.encode("utf-8")
    finally:
        # Make sure we always close the upstream stream & send [DONE]
        try:
            close_coro = getattr(stream, "aclose", None)
            if asyncio.iscoroutinefunction(close_coro):
                await close_coro()
        except Exception:  # pragma: no cover - best effort
            logger.exception("Error while closing OpenAI stream")

        yield b"data: [DONE]\n\n"


@router.post("/responses")
async def create_response(
    request: Request,
    body: Dict[str, Any] = Body(
        ...,
        description=(
            "Arbitrary JSON payload forwarded to OpenAI's /v1/responses. "
            "If `stream` is truthy, this route returns Server‑Sent Events."
        ),
    ),
) -> Any:
    """
    /v1/responses relay route.

    Behaviour:
    - If `body.get("stream")` is falsy/missing: behave like a normal JSON proxy and
      return the upstream OpenAI response as JSON.
    - If `stream` is truthy: call OpenAI with `stream=True` and forward the
      resulting AsyncStream as an SSE stream (`text/event-stream`).
    """
    logger.info("Incoming /v1/responses request")

    stream_param = body.get("stream")

    # Treat any truthy value as "please stream"
    if stream_param:
        logger.info("Handling /v1/responses as streaming SSE request")

        # IMPORTANT:
        # - We *do* forward `stream=True` to OpenAI so it returns an AsyncStream.
        # - forward_responses_create() wraps non-streaming responses in plain dicts,
        #   but when `stream=True` it returns the raw AsyncStream unchanged, which
        #   is exactly what we want here.
        upstream_stream = await forward_responses_create(body)

        # And we NEVER return the AsyncStream directly – we wrap it in a
        # StreamingResponse that yields SSE frames.
        return StreamingResponse(
            _iter_sse_events(upstream_stream),
            media_type="text/event-stream",
            headers={
                # Standard SSE friendliness
                "Cache-Control": "no-cache",
                # Disable buffering for some reverse proxies
                "X-Accel-Buffering": "no",
            },
        )

    # Non-streaming: just proxy through and let FastAPI JSON-encode the result
    logger.info("Handling /v1/responses as non-streaming JSON request")
    return await forward_responses_create(body)
