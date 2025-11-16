"""
passthrough_proxy.py — SSE and streaming passthrough layer
───────────────────────────────────────────────────────────
Legacy helper for /v1/responses streaming relay.

NOTE:
  • forward_openai_request already handles streaming for all endpoints.
  • Keep this only if you explicitly wire it to /v1/responses routes.
"""

import os
import httpx
from fastapi import Request
from starlette.responses import StreamingResponse
from app.utils.logger import relay_log as logger

DEFAULT_OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com")


# Helper added for testing and mock patching
async def upstream_sse_stream(*args, **kwargs):
    yield 'data: {"mock": true}\n\n'
    yield "data: [DONE]\n\n"


async def passthrough_sse(request: Request) -> StreamingResponse:
    """
    Stream server-sent events from OpenAI `/v1/responses` back to the client.
    """
    # Normalize accidental /v1/v1/ duplication
    path = request.url.path.replace("/v1/v1/", "/v1/")
    api_base = getattr(request.app.state, "OPENAI_API_BASE", DEFAULT_OPENAI_API_BASE)
    upstream_url = f"{api_base.rstrip('/')}{path}"

    body = await request.body()
    headers = {
        "Authorization": request.headers.get("authorization", ""),
        "Content-Type": request.headers.get("content-type", "application/json"),
        "Accept": "text/event-stream",
    }

    async def event_generator():
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                method=request.method,
                url=upstream_url,
                headers=headers,
                content=body,
            ) as response:
                logger.info(f"Streaming from {upstream_url} — {response.status_code}")
                async for chunk in response.aiter_text():
                    if chunk:
                        yield chunk

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )
