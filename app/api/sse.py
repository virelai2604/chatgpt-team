from __future__ import annotations

import json
from typing import Any, AsyncIterator, Dict

from fastapi import APIRouter, Request
from starlette.responses import StreamingResponse

from app.core.http_client import get_async_openai_client
from app.core.config import get_settings

router = APIRouter(prefix="/v1", tags=["sse"])


def _sse_pack(data: Dict[str, Any]) -> bytes:
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n".encode("utf-8")


async def _responses_event_stream(payload: Dict[str, Any]) -> AsyncIterator[bytes]:
    """
    Streams OpenAI Responses events as SSE.

    Ensures the client sees standard "data: {...}\\n\\n" frames and terminates with [DONE].
    """
    client = get_async_openai_client()
    # Force streaming
    payload = dict(payload)
    payload["stream"] = True

    stream = await client.responses.create(**payload)  # type: ignore[arg-type]
    async for event in stream:
        # event is a pydantic model in openai-python; model_dump() is preferred
        if hasattr(event, "model_dump"):
            data = event.model_dump()
        else:
            data = {"type": getattr(event, "type", "unknown"), "event": str(event)}
        yield _sse_pack(data)

    yield b"data: [DONE]\n\n"


@router.post("/responses:stream")
async def responses_stream(request: Request) -> StreamingResponse:
    settings = get_settings()
    payload = await request.json()
    payload.setdefault("model", settings.DEFAULT_MODEL)

    return StreamingResponse(
        _responses_event_stream(payload),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache"},
    )
