"""
realtime.py — OpenAI-Compatible /v1/realtime/sessions/events Endpoint
─────────────────────────────────────────────────────────────────────
Provides full Server-Sent Events (SSE) passthrough for real-time sessions.

Aligned with:
  • openai-python SDK v2.61
  • openai-node SDK v6.7.0
  • OpenAI API Reference (2025-10)

Supports:
  • GET /v1/realtime/sessions/events   → stream live events (SSE)
  • POST /v1/realtime/sessions/events  → send event to active session

Implements:
  • bidirectional stream handling
  • graceful client disconnect
  • consistent error schema
"""

import os
import asyncio
import httpx
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse, JSONResponse
from app.utils.logger import log

router = APIRouter(prefix="/v1/realtime/sessions", tags=["realtime"])

OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
USER_AGENT = "openai-python/2.61.0"
RELAY_TIMEOUT = float(os.getenv("RELAY_TIMEOUT", 300))

# ------------------------------------------------------------
# Common headers
# ------------------------------------------------------------
def build_headers(content_type="application/json"):
    return {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "User-Agent": USER_AGENT,
        "Accept": "text/event-stream",
        "Content-Type": content_type,
    }


# ------------------------------------------------------------
# GET /v1/realtime/sessions/events → stream events
# ------------------------------------------------------------
@router.get("/events")
async def stream_realtime_events(request: Request):
    """
    Opens a streaming SSE connection to the upstream OpenAI Realtime API.
    Mirrors client.realtime.sessions.events.list() in SDKs.
    """
    upstream_url = f"{OPENAI_API_BASE}/realtime/sessions/events"
    headers = build_headers()

    log.info("[Realtime] Establishing SSE connection to OpenAI Realtime API...")

    async with httpx.AsyncClient(timeout=None) as client:
        try:
            upstream_resp = await client.get(upstream_url, headers=headers)
        except httpx.RequestError as e:
            log.error(f"[Realtime] Connection failed: {e}")
            return JSONResponse(
                {"error": {"message": str(e), "type": "network_error"}},
                status_code=502,
            )

        # Verify streaming header
        if "text/event-stream" not in upstream_resp.headers.get("content-type", ""):
            log.warning("[Realtime] Upstream did not return SSE.")
            try:
                data = upstream_resp.json()
                return JSONResponse(data, status_code=upstream_resp.status_code)
            except Exception:
                return JSONResponse(
                    {"error": "Unexpected upstream response", "raw": upstream_resp.text[:1000]},
                    status_code=upstream_resp.status_code,
                )

        # Stream events
        async def event_generator():
            try:
                async for chunk in upstream_resp.aiter_bytes():
                    if await request.is_disconnected():
                        log.info("[Realtime] Client disconnected.")
                        break
                    yield chunk
            except asyncio.CancelledError:
                log.warning("[Realtime] Stream cancelled by server.")
            except Exception as e:
                log.error(f"[Realtime] Stream error: {e}")
                yield f"event: error\ndata: {{\"message\": \"{str(e)}\"}}\n\n".encode()

        log.info("[Realtime] Stream established successfully.")
        return StreamingResponse(event_generator(), media_type="text/event-stream")


# ------------------------------------------------------------
# POST /v1/realtime/sessions/events → send event to session
# ------------------------------------------------------------
@router.post("/events")
async def send_realtime_event(request: Request):
    """
    Sends a client event to the current realtime session.
    Mirrors client.realtime.sessions.events.create() in SDKs.
    """
    try:
        payload = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON body"}, status_code=400)

    headers = build_headers()
    upstream_url = f"{OPENAI_API_BASE}/realtime/sessions/events"

    async with httpx.AsyncClient(timeout=RELAY_TIMEOUT) as client:
        try:
            resp = await client.post(upstream_url, headers=headers, json=payload)
            log.info(f"[Realtime] Event sent, status={resp.status_code}")
            return JSONResponse(resp.json(), status_code=resp.status_code)
        except httpx.RequestError as e:
            log.error(f"[Realtime] Network error sending event: {e}")
            return JSONResponse(
                {"error": {"message": str(e), "type": "network_error"}},
                status_code=502,
            )
