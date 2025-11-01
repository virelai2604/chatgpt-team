# ==========================================================
# app/api/forward_openai.py — OpenAI API Forwarder (v2025.11)
# ==========================================================
"""
Handles all outgoing HTTP requests to the OpenAI API.
Supports:
  • JSON and multipart/form-data
  • Full streaming passthrough (SSE)
  • Unified error handling
  • Header propagation for OpenAI-Beta / Org / UA

Aligned with:
  - OpenAI REST API (Nov 2025)
  - openai-python SDK >= v1.51
"""

import os
import json
import httpx
from fastapi import Request, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse

# ----------------------------------------------------------
# Environment Configuration
# ----------------------------------------------------------
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise RuntimeError("Missing OPENAI_API_KEY environment variable")

DEFAULT_HEADERS = {
    "Authorization": f"Bearer {OPENAI_API_KEY}",
    "User-Agent": "ChatGPT-Team-Relay/2025.11",
    "Accept": "application/json",
}


# ----------------------------------------------------------
# Helper: Stream passthrough
# ----------------------------------------------------------
async def _stream_response(client: httpx.AsyncClient, method: str, url: str, **kwargs):
    """Pass streaming responses through directly to the client."""
    async with client.stream(method, url, **kwargs) as resp:
        if resp.status_code >= 400:
            text = await resp.aread()
            raise HTTPException(status_code=resp.status_code, detail=text.decode(errors="ignore"))

        async for chunk in resp.aiter_text():
            yield chunk


# ----------------------------------------------------------
# Main Forwarder
# ----------------------------------------------------------
async def forward_openai_request(
    path: str,
    body: dict | None = None,
    stream: bool = False,
    request: Request | None = None,
):
    """
    Forwards a request to the OpenAI API, preserving all relevant headers and body.
    Supports both standard and streaming (SSE) responses.
    """
    url = f"{OPENAI_BASE_URL.rstrip('/')}{path}"
    method = request.method if request else "POST"

    # Base headers
    headers = DEFAULT_HEADERS.copy()
    headers.update({
        "User-Agent": request.headers.get("User-Agent", "ChatGPT-Team-Relay/2025.11"),
        "OpenAI-Organization": request.headers.get("OpenAI-Organization", ""),
        "OpenAI-Beta": request.headers.get("OpenAI-Beta", ""),
    })

    content = None
    data = None
    files = None

    # Parse content-type and build request payload
    if request:
        method = request.method
        ctype = request.headers.get("content-type", "").lower()

        if ctype.startswith("multipart/form-data"):
            form = await request.form()
            files = []
            data = {}
            for field, value in form.multi_items():
                if hasattr(value, "filename") and value.filename:
                    files.append(
                        (
                            field,
                            (value.filename, await value.read(), value.content_type or "application/octet-stream"),
                        )
                    )
                else:
                    data[field] = value

        elif ctype.startswith("application/json"):
            try:
                body = await request.json()
            except Exception:
                body = None
            content = json.dumps(body) if body is not None else None
            headers["Content-Type"] = "application/json"
    elif body is not None:
        content = json.dumps(body)
        headers["Content-Type"] = "application/json"

    # ------------------------------------------------------
    # Execute request
    # ------------------------------------------------------
    try:
        timeout = httpx.Timeout(300.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            # Streaming (SSE) passthrough
            if stream:
                return StreamingResponse(
                    _stream_response(client, method, url, headers=headers, content=content, data=data, files=files),
                    media_type="text/event-stream",
                )

            # Standard request
            resp = await client.request(method, url, headers=headers, content=content, data=data, files=files)

            try:
                payload = resp.json()
            except Exception:
                payload = {"raw": (await resp.aread()).decode(errors="ignore")}

            if resp.status_code >= 400:
                raise HTTPException(status_code=resp.status_code, detail=payload)

            return JSONResponse(content=payload, status_code=resp.status_code)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Forwarding error: {e}")
