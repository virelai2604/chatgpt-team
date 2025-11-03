"""
realtime.py — Proxy handler for OpenAI-compatible realtime session streams.

This module implements `/v1/realtime/sessions/events`,
forwarding live event streams (SSE) directly from the upstream OpenAI API.
"""

import os
import httpx
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse, JSONResponse
from app.utils.logger import log

router = APIRouter()

OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

@router.get("/v1/realtime/sessions/events")
async def realtime_stream(request: Request):
    """
    Forwards Server-Sent Events (SSE) from OpenAI’s Realtime API
    to the client in a live stream.
    """
    log.info("[P4] Handling GET /v1/realtime/sessions/events")

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Accept": "text/event-stream",
    }

    async with httpx.AsyncClient(timeout=None) as client:
        try:
            upstream_resp = await client.get(
                f"{OPENAI_API_BASE}/realtime/sessions/events",
                headers=headers,
                timeout=None,
            )

            if upstream_resp.status_code != 200:
                log.warning(f"[P4] Upstream returned {upstream_resp.status_code} for /realtime/sessions/events")
                return JSONResponse(
                    {
                        "error": "Upstream returned non-200 response",
                        "status": upstream_resp.status_code,
                    },
                    status_code=upstream_resp.status_code,
                )

            async def event_streamer():
                async for chunk in upstream_resp.aiter_text():
                    if await request.is_disconnected():
                        log.info("[P4] Client disconnected from realtime stream.")
                        break
                    yield chunk

            log.info("[P4] Upstream realtime stream established → 200")
            return StreamingResponse(event_streamer(), media_type="text/event-stream")

        except Exception as e:
            log.error(f"[P4] Realtime streaming error: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)
