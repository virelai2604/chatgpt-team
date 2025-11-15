"""
responses.py — /v1/responses
─────────────────────────────
Implements OpenAI-compatible Responses API with full streaming support.
"""

import os
import json
import httpx
import asyncio
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse
from app.utils.logger import log

router = APIRouter(prefix="/v1", tags=["responses"])

OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
USER_AGENT = "openai-python/2.8.0"
TIMEOUT = float(os.getenv("RELAY_TIMEOUT", 120))

@router.post("/responses")
async def create_response(request: Request):
    """Relays a response creation request to OpenAI."""
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

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            resp = await client.post(url, headers=headers, json=body)
        except httpx.RequestError as e:
            log.error(f"[Responses] network error: {e}")
            return JSONResponse({"error": {"message": str(e)}}, status_code=502)

        if stream and "text/event-stream" in resp.headers.get("content-type", ""):
            async def sse_stream():
                async for chunk in resp.aiter_text():
                    if await request.is_disconnected():
                        break
                    yield chunk
            return StreamingResponse(sse_stream(), media_type="text/event-stream")

        return JSONResponse(resp.json(), status_code=resp.status_code)
