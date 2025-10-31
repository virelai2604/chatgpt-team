# ==========================================================
# app/api/passthrough_proxy.py — Ground Truth Passthrough Proxy (v2025.11)
# ==========================================================
"""
Fallback route handler for undefined /v1 endpoints.

Forwards arbitrary HTTP requests to the configured OpenAI-compatible API,
while translating known deprecated responses (e.g. 410 → 404).
"""

import os
import httpx
import logging
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse

OPENAI_BASE = os.getenv("OPENAI_BASE_URL", "https://api.openai.com")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
TIMEOUT = float(os.getenv("OPENAI_TIMEOUT", "180.0"))

router = APIRouter(tags=["Passthrough Proxy"])
logger = logging.getLogger("passthrough_proxy")

headers = {
    "Authorization": f"Bearer {OPENAI_API_KEY}",
    "Content-Type": "application/json",
}


# ----------------------------------------------------------
# Core Passthrough Logic
# ----------------------------------------------------------
async def _passthrough(method: str, path: str, data=None, stream=False):
    """Generic OpenAI-compatible request forwarder."""
    url = f"{OPENAI_BASE}{path}"
    logger.info(f"🌐 Passthrough proxy → {url} [{method}]")

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            response = await client.request(method, url, headers=headers, json=data)
        except Exception as e:
            logger.error(f"Passthrough network error: {e}")
            return JSONResponse({"error": "Network error", "detail": str(e)}, status_code=500)

        # Translate deprecated status codes
        if response.status_code == 410:
            return JSONResponse({"detail": "Deprecated endpoint"}, status_code=404)
        if response.status_code == 404:
            return JSONResponse({"detail": "Not found"}, status_code=404)
        if response.status_code >= 500:
            return JSONResponse({"detail": f"Upstream error {response.status_code}"}, status_code=500)

        # Handle streaming
        if stream and "text/event-stream" in response.headers.get("content-type", ""):
            return StreamingResponse(response.aiter_text(), media_type="text/event-stream")

        # Return JSON or text fallback
        try:
            return JSONResponse(response.json())
        except Exception:
            return JSONResponse({"detail": response.text}, status_code=response.status_code)


# ----------------------------------------------------------
# Catch-All Route for /v1/*
# ----------------------------------------------------------
@router.api_route("/v1/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def passthrough_proxy(request: Request, path: str):
    """Catch-all passthrough handler for all undefined /v1 routes."""
    method = request.method
    try:
        data = await request.json()
    except Exception:
        data = None

    stream = "text/event-stream" in request.headers.get("accept", "")
    return await _passthrough(method, f"/v1/{path}", data=data, stream=stream)
