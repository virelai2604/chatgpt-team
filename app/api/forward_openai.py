# ==========================================================
# app/api/forward_openai.py — Ground Truth Edition (Final)
# ==========================================================
"""
Unified OpenAI proxy adapter for ChatGPT Team Relay.
Handles forwarding for all API endpoints — including:
  • JSON POST/GET/PATCH/DELETE requests
  • Multipart file uploads
  • SSE streaming for responses
This module ensures consistent error handling and parity with
OpenAI’s official API behavior (2025.10).
"""

import os
import logging
import httpx
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi import HTTPException

# ----------------------------------------------------------
# Environment setup
# ----------------------------------------------------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com")
TIMEOUT = float(os.getenv("FORWARD_TIMEOUT", 120.0))

if not OPENAI_API_KEY:
    logging.warning("[WARN] OPENAI_API_KEY not found; relay will fail on OpenAI calls.")

# ----------------------------------------------------------
# Core forwarding logic
# ----------------------------------------------------------
async def forward_openai_request(
    path: str,
    method: str = "GET",
    json: dict | None = None,
    data: dict | None = None,
    files: dict | None = None,
    stream: bool = False,
):
    """
    Forwards requests to the OpenAI API, supporting:
      - Standard JSON payloads
      - Multipart form uploads
      - SSE (streaming responses)
    Returns FastAPI JSONResponse or StreamingResponse.
    """

    url = f"{OPENAI_BASE_URL.rstrip('/')}/{path.lstrip('/')}"
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(TIMEOUT)) as client:

            # ---- FILE UPLOAD OR FORM DATA ----
            if files or data:
                resp = await client.request(
                    method,
                    url,
                    headers=headers,
                    data=data,
                    files=files,
                )
                return JSONResponse(content=_safe_json(resp), status_code=resp.status_code)

            # ---- STREAM MODE ----
            if stream:
                async with client.stream(method, url, json=json, headers=headers) as upstream:
                    if upstream.status_code != 200:
                        body = await upstream.aread()
                        raise HTTPException(status_code=upstream.status_code, detail=body.decode())
                    return StreamingResponse(
                        upstream.aiter_text(),
                        media_type="text/event-stream"
                    )

            # ---- STANDARD JSON ----
            resp = await client.request(method, url, json=json, headers=headers)
            return JSONResponse(content=_safe_json(resp), status_code=resp.status_code)

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Upstream request timed out.")
    except HTTPException:
        raise  # already properly handled
    except Exception as e:
        logging.exception(f"[Relay] Unexpected forwarding error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ----------------------------------------------------------
# Helper: safely parse any OpenAI response JSON
# ----------------------------------------------------------
def _safe_json(response: httpx.Response) -> dict:
    """Return parsed JSON or raw text for debugging."""
    try:
        return response.json()
    except Exception:
        return {"error": response.text}
