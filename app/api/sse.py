# app/api/sse.py
from __future__ import annotations

import json
from typing import Any, AsyncIterator


def format_sse_event(event: str, data: Any) -> bytes:
    """
    Format a single Server-Sent Event (SSE) frame.

    Produces bytes of the form:
        event: <event>\n
        data: <json-data>\n
        \n

    This is handy for emitting synthetic events (e.g. fallback errors)
    while still looking like OpenAI's SSE frames.
    """
    if isinstance(data, str):
        data_str = data
    else:
        data_str = json.dumps(data, separators=(",", ":"))

    lines = [
        f"event: {event}",
        f"data: {data_str}",
        "",  # blank line terminator
    ]
    return ("\n".join(lines) + "\n").encode("utf-8")


async def proxy_sse_bytes(
    upstream_iter: AsyncIterator[bytes],
) -> AsyncIterator[bytes]:
    """
    Simple SSE byte proxy:

    - Accepts raw byte chunks from an upstream streaming response.
    - Yields them as-is (filtering out empty keepalives).

    This keeps the relay transparent: we don't reinterpret OpenAI's
    SSE framing, we just pass it through.
    """
    async for chunk in upstream_iter:
        if not chunk:
            continue
        yield chunk
