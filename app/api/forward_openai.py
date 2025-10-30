# ==========================================================
# forward_openai.py — Universal Forwarder for OpenAI Requests
# ==========================================================
"""
Handles all outbound HTTP requests to the OpenAI API,
with full support for JSON, multipart/form-data, and
Server-Sent Events (SSE) streaming.

Ground Truth 2025.10 aligned.
"""

import os
import httpx
import asyncio
import logging
from fastapi.responses import StreamingResponse, JSONResponse

logger = logging.getLogger("forwarder")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = "https://api.openai.com/"

if not OPENAI_API_KEY:
    logger.warning("[WARN] OPENAI_API_KEY not found in environment.")

# ==========================================================
# Stream generator for SSE responses
# ==========================================================

async def event_generator(method, url, headers=None, json=None, data=None, files=None):
    """
    Streams Server-Sent Events (SSE) from OpenAI in real time.
    """
    try:
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream(method, url, headers=headers, json=json, data=data, files=files) as response:
                async for line in response.aiter_lines():
                    if line.strip():
                        yield f"{line}\n"
    except Exception as e:
        logger.error(f"[Relay] Stream error: {e}")
        yield f"data: [Relay] Stream error: {str(e)}\n\n"
        return


# ==========================================================
# Forward Request Core
# ==========================================================

async def forward_openai_request(
    path: str,
    method: str = "GET",
    json_data=None,
    data=None,
    files=None,
    stream: bool = False,
):
    """
    Sends the given request to the OpenAI API.
    Handles both standard JSON responses and streaming responses.
    """

    url = f"{OPENAI_BASE_URL}{path}"
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}

    # Decide how to send
    try:
        async with httpx.AsyncClient(timeout=None) as client:
            if stream:
                # Return async generator directly for FastAPI StreamingResponse
                return event_generator(method, url, headers=headers, json=json_data, data=data, files=files)

            # Normal non-streaming
            response = await client.request(method, url, headers=headers, json=json_data, data=data, files=files)
            response.raise_for_status()

            # Return parsed JSON
            return response.json()

    except httpx.HTTPStatusError as e:
        logger.error(f"[Relay] OpenAI API Error ({e.response.status_code}): {e.response.text}")
        return {
            "status_code": e.response.status_code,
            "error": e.response.json(),
            "path": path,
            "method": method,
        }

    except Exception as e:
        logger.exception(f"[Relay] Unexpected error while forwarding request: {e}")
        return {
            "ok": False,
            "status_code": 500,
            "upstream_error": str(e),
            "path": path,
            "method": method,
        }
