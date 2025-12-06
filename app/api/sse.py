# app/api/sse.py

from __future__ import annotations

import json
from typing import Any, AsyncIterator, Dict, Iterable, Optional, Union

from fastapi import APIRouter, Body
from fastapi.responses import StreamingResponse

from app.core.http_client import get_async_openai_client
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/v1", tags=["openai-relay-streaming"])

SSEByteSource = Union[Iterable[bytes], AsyncIterator[bytes]]


def format_sse_event(
    *,
    event: str,
    data: str,
    id: Optional[str] = None,
    retry: Optional[int] = None,
) -> bytes:
    """
    Format a single Server-Sent Event (SSE) frame.

    Output format (UTF-8):
        id: <id>
        event: <event>
        data: <line1>
        data: <line2>
        retry: <retry>

    Followed by a blank line.
    """
    lines = []

    if id is not None:
        lines.append(f"id: {id}")

    if event:
        lines.append(f"event: {event}")

    if data == "":
        lines.append("data:")
    else:
        for line in data.splitlines():
            lines.append(f"data: {line}")

    if retry is not None:
        lines.append(f"retry: {retry}")

    payload = "\n".join(lines) + "\n\n"
    return payload.encode("utf-8")


def sse_error_event(
    message: str,
    code: Optional[str] = None,
    *,
    id: Optional[str] = None,
) -> bytes:
    """
    Convenience helper for emitting an SSE 'error' event.
    """
    payload = {"message": message}
    if code:
        payload["code"] = code

    data_parts = [f"{k}={v}" for k, v in payload.items()]
    data_str = ";".join(data_parts)

    return format_sse_event(event="error", data=data_str, id=id)


class StreamingSSE(StreamingResponse):
    """
    StreamingResponse wrapper that fixes the media type to `text/event-stream`
    and expects an iterator/async-iterator of bytes.
    """

    def __init__(
        self,
        content: SSEByteSource,
        status_code: int = 200,
        headers: Optional[dict] = None,
    ) -> None:
        super().__init__(
            content=content,
            status_code=status_code,
            headers=headers,
            media_type="text/event-stream",
        )


async def _responses_event_stream(payload: Dict[str, Any]) -> AsyncIterator[bytes]:
    """
    SSE bridge for the OpenAI Responses streaming API.

    Expects the same body as /v1/responses, but will:
      - call client.responses.create(..., stream=True)
      - emit each event as a JSON server-sent event: `data: {...}\n\n`
      - terminate with `data: [DONE]\n\n`
    """
    client = get_async_openai_client()
    logger.info("Streaming /v1/responses:stream with payload: %s", payload)

    payload = dict(payload)
    payload.setdefault("stream", True)

    stream = await client.responses.create(**payload)  # stream=True above

    async for event in stream:
        if hasattr(event, "model_dump_json"):
            data_json = event.model_dump_json()
        elif hasattr(event, "model_dump"):
            data_dict = event.model_dump()
            data_json = json.dumps(data_dict, default=str, separators=(",", ":"))
        else:
            try:
                data_json = json.dumps(event, default=str, separators=(",", ":"))
            except TypeError:
                data_json = json.dumps(str(event))

        chunk = f"data: {data_json}\n\n"
        yield chunk.encode("utf-8")

    yield b"data: [DONE]\n\n"


@router.post("/responses:stream")
async def responses_stream(
    body: Dict[str, Any] = Body(..., description="OpenAI Responses.create payload for streaming"),
) -> StreamingSSE:
    """
    SSE streaming endpoint for the Responses API.

    Mirrors the OpenAI Python SDK streaming usage:
        stream = client.responses.create(..., stream=True)
        for event in stream: ...
    """
    return StreamingSSE(_responses_event_stream(body))
