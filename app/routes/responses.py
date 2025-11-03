"""
responses.py — OpenAI-Compatible /v1/responses Endpoint
────────────────────────────────────────────────────────────
Implements the full /v1/responses relay for the ChatGPT Team Relay.
Conforms to:
  • openai-python SDK v2.61
  • OpenAI API Reference (2025-10)
Supports:
  • sync + streaming (SSE)
  • chain continuation
  • structured error output
"""

import os
import json
import httpx
import asyncio
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse
from app.utils.logger import log

router = APIRouter(prefix="/v1", tags=["responses"])

# ------------------------------------------------------------
# Environment
# ------------------------------------------------------------
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
RELAY_TIMEOUT = float(os.getenv("RELAY_TIMEOUT", 120))
USER_AGENT = "openai-python/2.61.0"

# ------------------------------------------------------------
# POST /v1/responses
# ------------------------------------------------------------
@router.post("/responses")
async def create_response(request: Request):
    """Relay synchronous and streaming response creation to OpenAI."""
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON body"}, status_code=400)

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "User-Agent": USER_AGENT,
        "Content-Type": "application/json",
    }

    stream = bool(body.get("stream"))
    url = f"{OPENAI_API_BASE}/responses"

    async with httpx.AsyncClient(timeout=RELAY_TIMEOUT) as client:
        try:
            resp = await client.post(url, headers=headers, json=body)
        except httpx.RequestError as e:
            log.error(f"Network error contacting OpenAI: {e}")
            return JSONResponse(
                {"error": {"message": str(e), "type": "network_error"}},
                status_code=502,
            )

        # --- Streaming (SSE) ---
        if stream and "text/event-stream" in resp.headers.get("content-type", ""):
            async def sse_stream():
                try:
                    async for chunk in resp.aiter_text():
                        if await request.is_disconnected():
                            log.info("🔌 client disconnected mid-stream")
                            break
                        yield chunk
                except asyncio.TimeoutError:
                    yield "event: error\ndata: {\"message\": \"Stream timeout\"}\n\n"
            log.info("✅ streaming relay established")
            return StreamingResponse(sse_stream(), media_type="text/event-stream")

        # --- Non-streaming JSON ---
        try:
            return JSONResponse(resp.json(), status_code=resp.status_code)
        except Exception:
            return JSONResponse(
                {
                    "error": "Invalid JSON from upstream",
                    "raw": resp.text[:500],
                    "status": resp.status_code,
                },
                status_code=resp.status_code,
            )

# ------------------------------------------------------------
# POST /v1/responses/chain/{previous_id}
# ------------------------------------------------------------
@router.post("/responses/chain/{previous_id}")
async def chain_response(previous_id: str, request: Request):
    """Chain a new response from a previous response (context continuation)."""
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON body"}, status_code=400)

    body["previous_response_id"] = previous_id
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "User-Agent": USER_AGENT,
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=RELAY_TIMEOUT) as client:
        try:
            resp = await client.post(f"{OPENAI_API_BASE}/responses", headers=headers, json=body)
            return JSONResponse(resp.json(), status_code=resp.status_code)
        except httpx.RequestError as e:
            return JSONResponse(
                {"error": {"message": str(e), "type": "network_error"}},
                status_code=502,
            )
