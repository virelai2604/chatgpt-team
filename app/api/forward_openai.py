# ==========================================================
# app/api/forward_openai.py — Ground Truth Edition (Final)
# ==========================================================
"""
Unified OpenAI request forwarder for ChatGPT Team Relay.
Handles:
  - JSON and multipart requests
  - Server-Sent Events (SSE) for streaming
  - Standardized error handling
"""

import os
import logging
import httpx
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi import HTTPException

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com")
TIMEOUT = float(os.getenv("FORWARD_TIMEOUT", 120.0))

logger = logging.getLogger("forward_openai")


async def forward_openai_request(
    path: str,
    method: str = "GET",
    json: dict | None = None,
    data: dict | None = None,
    files: dict | None = None,
    stream: bool = False,
):
    """
    Forward an arbitrary OpenAI-compatible request.
    """
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=401, detail="OPENAI_API_KEY not configured")

    url = f"{OPENAI_BASE_URL.rstrip('/')}/{path.lstrip('/')}"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Accept": "application/json, text/event-stream",
    }

    async def _iter_sse(resp):
        try:
            async for chunk in resp.aiter_text():
                yield chunk
        except Exception as e:
            logger.warning(f"[Stream interrupted] {e}")

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(TIMEOUT)) as client:
            # Multipart (e.g., file upload)
            if files or data:
                resp = await client.request(method, url, headers=headers, data=data, files=files)
                return JSONResponse(_safe_json(resp), status_code=resp.status_code)

            # Streaming (SSE)
            if stream:
                async with client.stream(method, url, json=json, headers=headers) as resp:
                    if resp.status_code != 200:
                        raise HTTPException(status_code=resp.status_code, detail=await resp.aread())
                    return StreamingResponse(_iter_sse(resp), media_type="text/event-stream")

            # Normal JSON
            resp = await client.request(method, url, json=json, headers=headers)
            return JSONResponse(_safe_json(resp), status_code=resp.status_code)

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="OpenAI request timed out")
    except Exception as e:
        logger.exception(f"[Forward error] {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _safe_json(resp: httpx.Response) -> dict:
    """Attempt to parse JSON safely."""
    try:
        return resp.json()
    except Exception:
        return {"status_code": resp.status_code, "text": resp.text}
