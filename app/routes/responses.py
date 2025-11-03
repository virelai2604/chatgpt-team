"""
responses.py — Core OpenAI-compatible /v1/responses route handler
with streaming and chain continuation support.
"""

import os
import json
import httpx
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse, JSONResponse

router = APIRouter()

OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ─────────────────────────────────────────────
# Streaming relay: forward SSE directly to client
# ─────────────────────────────────────────────
@router.post("/v1/responses")
async def relay_responses(request: Request):
    """Relay POST /v1/responses requests to OpenAI, supporting stream=True."""
    try:
        payload = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON body"}, status_code=400)

    stream = payload.get("stream", False)
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=None) as client:
        if stream:
            # Stream the response directly (SSE passthrough)
            upstream_resp = await client.post(
                f"{OPENAI_API_BASE}/responses",
                headers=headers,
                json=payload,
                timeout=None,
            )

            async def event_generator():
                async for chunk in upstream_resp.aiter_text():
                    yield chunk

            return StreamingResponse(event_generator(), media_type="text/event-stream")

        else:
            # Non-streaming mode: proxy full JSON
            resp = await client.post(
                f"{OPENAI_API_BASE}/responses",
                headers=headers,
                json=payload,
                timeout=None,
            )
            return JSONResponse(resp.json(), status_code=resp.status_code)

# ─────────────────────────────────────────────
# Chain continuation: reuse previous response.id
# ─────────────────────────────────────────────
@router.post("/v1/responses/chain/{previous_id}")
async def relay_chain(previous_id: str, request: Request):
    """
    Chain a response using a previous /v1/responses result.
    Automatically reuses context or metadata from the last call.
    """
    try:
        payload = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON body"}, status_code=400)

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    # Insert the previous response ID to maintain chain continuity
    payload["previous_response_id"] = previous_id

    async with httpx.AsyncClient(timeout=None) as client:
        resp = await client.post(
            f"{OPENAI_API_BASE}/responses",
            headers=headers,
            json=payload,
            timeout=None,
        )
        return JSONResponse(resp.json(), status_code=resp.status_code)
