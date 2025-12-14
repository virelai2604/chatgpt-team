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


def sse_error_event(message: str, code: Optional[str] = None, *, id: Optional[str] = None) -> bytes:
    payload = {"message": message}
    if code:
        payload["code"] = code
    data_str = ";".join([f"{k}={v}" for k, v in payload.items()])
    return format_sse_event(event="error", data=data_str, id=id)


class StreamingSSE(StreamingResponse):
    def __init__(self, content: SSEByteSource, status_code: int = 200, headers: Optional[dict] = None) -> None:
        super().__init__(content=content, status_code=status_code, headers=headers, media_type="text/event-stream")


# Compatibility shim: some older modules imported create_sse_stream from app.api.sse
def create_sse_stream(
    content: SSEByteSource,
    *,
    status_code: int = 200,
    headers: Optional[dict] = None,
) -> StreamingSSE:
    return StreamingSSE(content=content, status_code=status_code, headers=headers)


async def _responses_event_stream(payload: Dict[str, Any]) -> AsyncIterator[bytes]:
    client = get_async_openai_client()
    logger.info("Streaming /v1/responses:stream with payload: %s", payload)

    p = dict(payload)
    p.setdefault("stream", True)

    stream = await client.responses.create(**p)  # stream=True above

    async for event in stream:
        if hasattr(event, "model_dump_json"):
            data_json = event.model_dump_json()
        elif hasattr(event, "model_dump"):
            data_json = json.dumps(event.model_dump(), default=str, separators=(",", ":"))
        else:
            try:
                data_json = json.dumps(event, default=str, separators=(",", ":"))
            except TypeError:
                data_json = json.dumps(str(event))

        yield f"data: {data_json}\n\n".encode("utf-8")

    yield b"data: [DONE]\n\n"


@router.post("/responses:stream")
async def responses_stream(
    body: Dict[str, Any] = Body(..., description="OpenAI Responses.create payload for streaming"),
) -> StreamingSSE:
    return StreamingSSE(_responses_event_stream(body))
