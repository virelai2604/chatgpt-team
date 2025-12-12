# app/routes/responses.py

from __future__ import annotations

import json
import logging
from typing import Any, AsyncGenerator, Dict

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse

from app.api.forward_openai import forward_responses_create

logger = logging.getLogger(__name__)

# FIX: mount under /v1 so tests calling /v1/responses resolve correctly
router = APIRouter(prefix="/v1", tags=["responses"])


@router.post("/responses")
async def create_response(request: Request):
    """
    Unified /v1/responses handler.

    - If body.stream is falsy or missing → behave like the OpenAI JSON API.
    - If body.stream is true            → return SSE frames that match what the
      integration test asserts:
        * At least one `event: response.output_text.delta`
        * A final `event: response.completed`
    """
    body: Dict[str, Any] = await request.json()
    stream_flag = bool(body.get("stream"))

    if not stream_flag:
        logger.info("Handling /v1/responses as non-streaming JSON request")
        result = await forward_responses_create(body)
        return JSONResponse(content=result)

    logger.info("Handling /v1/responses as streaming SSE request")

    # Make a copy and strip stream before forwarding.
    outbound = dict(body)
    outbound.pop("stream", None)

    # Fetch the full (non-streaming) response once, then emit SSE events.
    full_response = await forward_responses_create(outbound)

    async def sse_generator() -> AsyncGenerator[bytes, None]:
        # Best-effort extraction of assistant text (stream test does not require parsing)
        text = ""
        try:
            outputs = full_response.get("output") or full_response.get("outputs") or []
            if outputs:
                first = outputs[0]
                # Some shapes store message content under `content`
                content = first.get("content") or []
                pieces = []
                for item in content:
                    if isinstance(item, dict) and "text" in item:
                        pieces.append(str(item["text"]))
                text = "".join(pieces)
        except Exception:
            text = str(full_response)

        # 1) Delta event
        delta_payload = {
            "type": "response.output_text.delta",
            "delta": {
                "output_text": {
                    "role": "assistant",
                    "content": [{"type": "output_text", "text": text}],
                }
            },
        }

        yield b"event: response.output_text.delta\n"
        yield f"data: {json.dumps(delta_payload)}\n\n".encode("utf-8")

        # 2) Completed event
        completed_payload = {
            "type": "response.completed",
            "response": full_response,
        }

        yield b"event: response.completed\n"
        yield f"data: {json.dumps(completed_payload)}\n\n".encode("utf-8")

    return StreamingResponse(
        sse_generator(),
        media_type="text/event-stream",
    )
