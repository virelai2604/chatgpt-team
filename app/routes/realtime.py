"""
realtime.py — /v1/realtime/sessions/events
──────────────────────────────────────────
Passthrough SSE streaming + event posting for Realtime API.
"""

import os
import httpx
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse

router = APIRouter(prefix="/v1/realtime/sessions", tags=["realtime"])

OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

@router.get("/events")
async def stream_events(request: Request):
    async with httpx.AsyncClient(timeout=None) as client:
        resp = await client.get(f"{OPENAI_API_BASE}/realtime/sessions/events",
                                headers={"Authorization": f"Bearer {OPENAI_API_KEY}"})
        async def event_gen():
            async for chunk in resp.aiter_bytes():
                if await request.is_disconnected():
                    break
                yield chunk
        return StreamingResponse(event_gen(), media_type="text/event-stream")
