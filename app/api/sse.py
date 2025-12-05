# app/api/sse.py

from __future__ import annotations

import logging
from typing import AsyncIterator, Awaitable, Callable, Iterable, Optional, Union

from fastapi.responses import StreamingResponse

logger = logging.getLogger("relay")

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

    # SSE data can span multiple lines; each must be prefixed with "data: "
    if data == "":
        # Even empty data should still yield a data line
        lines.append("data:")
    else:
        for line in data.splitlines():
            lines.append(f"data: {line}")

    if retry is not None:
        lines.append(f"retry: {retry}")

    # End of event frame
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

    # JSON is fine, but keep it simple: key=value;key=value
    data_parts = [f"{k}={v}" for k, v in payload.items()]
    data_str = ";".join(data_parts)

    return format_sse_event(event="error", data=data_str, id=id)


class StreamingSSE(StreamingResponse):
    """
    Thin wrapper around StreamingResponse that fixes the media type to
    `text/event-stream` and expects an iterator/async-iterator of bytes.

    Usage:
        async def event_iter():
            yield format_sse_event(event="message", data="hello")

        return StreamingSSE(event_iter())
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
