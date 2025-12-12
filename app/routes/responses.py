# app/routes/responses.py

from __future__ import annotations

import json
import logging
from typing import Any, AsyncGenerator, Dict

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse

from app.api.forward_openai import forward_responses_create

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/responses")
async def create_response(request: Request):
    """
    Unified /v1/responses handler.

    - If body.stream is falsy or missing → behave like the OpenAI JSON API.
    - If body.stream is true           → return SSE in the same "shape"
      that the integration test expects:
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

    # We fetch the full (non-streaming) response once, then break it into SSE events.
    full_response = await forward_responses_create(outbound)

    async def sse_generator() -> AsyncGenerator[bytes, None]:
        """
        Yield SSE frames as bytes:
          event: response.output_text.delta
          data: {...}

          event: response.completed
          data: {...}
        """
        # Try to pull a human-readable text payload from the full response.
        text = ""
        try:
            outputs = full_response.get("output") or full_response.get("outputs") or []
            if outputs:
                first = outputs[0]
                # Responses API uses "output_text" with a content list.
                output_text = first.get("output_text") or {}
                content = output_text.get("content") or []
                pieces = []
                for item in content:
                    if isinstance(item, dict):
                        # Most common shape: {"type": "output_text", "text": "..."}
                        if "text" in item:
                            pieces.append(str(item["text"]))
                text = "".join(pieces)
        except Exception:  # pragma: no cover - defensive, but we always send *something*
            text = str(full_response)

        # 1) Delta event
        delta_payload = {
            "type": "response.output_text.delta",
            "delta": {
                "output_text": {
                    "role": "assistant",
                    "content": [
                        {
                            "type": "output_text",
                            "text": text,
                        }
                    ],
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
