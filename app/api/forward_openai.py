# ================================================================
# forward_openai.py — Ground Truth Passthrough Proxy (v2.1)
# ================================================================
# OpenAI-SDK-aligned proxy forwarder for ChatGPT Team Relay.
# Features:
#   • Matches official OpenAI SDK (v1.57.x) header + request pattern
#   • Handles multipart, JSON, SSE streaming, and error fallbacks
#   • Retries transient 5xx/429 responses
#   • Structured JSON logging for observability
#   • Clean shutdown hook
# ================================================================

import os
import time
import json
import asyncio
import httpx
import logging
from typing import Dict, Any
from fastapi import Request
from fastapi.responses import StreamingResponse, JSONResponse

logger = logging.getLogger("relay")

# ================================================================
# Environment Variables
# ================================================================
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_ORG_ID = os.getenv("OPENAI_ORG_ID")
RELAY_TIMEOUT = float(os.getenv("RELAY_TIMEOUT", 120))

# ================================================================
# Strict SDK-style Header Builder
# ================================================================
def _build_headers(method: str = "get") -> Dict[str, str]:
    """
    Construct headers exactly like the OpenAI Python SDK does.
    Avoids Cloudflare 400s by using a minimal, safe header set.
    """
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Accept": "application/json",
        "User-Agent": "openai-python/1.57.0",
    }

    # Org header only if provided
    if OPENAI_ORG_ID:
        headers["OpenAI-Organization"] = OPENAI_ORG_ID

    # Only attach Content-Type for write operations
    if method.lower() in {"post", "put", "patch"}:
        headers["Content-Type"] = "application/json"

    return headers


# ================================================================
# Core Forwarder
# ================================================================
async def forward_to_openai(request: Request, path: str) -> Any:
    """
    Forward a request to the OpenAI API, exactly matching SDK semantics.
    """

    method = request.method.lower()
    headers = _build_headers(method)

    # --- Normalize URL (avoid /v1/v1 duplication) ---
    base = OPENAI_API_BASE.rstrip("/")
    path = path.lstrip("/")
    if base.endswith("/v1") and path.startswith("v1/"):
        target_url = f"{base}/{path[3:].lstrip('/')}"
    else:
        target_url = f"{base}/{path}"

    # --- Prepare request body ---
    send_kwargs: Dict[str, Any] = {}
    if method in {"post", "put", "patch"}:
        content_type = request.headers.get("content-type", "").lower()

        if "multipart/form-data" in content_type:
            form = await request.form()
            data, files = {}, []
            for field, value in form.multi_items():
                if getattr(value, "filename", None):
                    files.append((field, (value.filename, value.file, value.content_type)))
                else:
                    data[field] = value
            send_kwargs = {"data": data, "files": files}
        else:
            body = await request.body()
            if body:
                send_kwargs = {"content": body}

    # --- Send request with retries ---
    start = time.perf_counter()
    async with httpx.AsyncClient(timeout=RELAY_TIMEOUT, follow_redirects=True) as client:
        for attempt in range(3):
            try:
                resp = await client.request(method, target_url, headers=headers, **send_kwargs)
                if resp.status_code not in {502, 503, 504, 429}:
                    break
                await asyncio.sleep(0.5 * (attempt + 1))
            except httpx.RequestError as e:
                if attempt == 2:
                    logger.error(f"❌ Network error contacting OpenAI: {e}")
                    return JSONResponse(
                        {
                            "error": {
                                "message": f"Request failed after retries: {e}",
                                "type": "network_error",
                                "code": "request_failed",
                            }
                        },
                        status_code=502,
                    )

    elapsed = (time.perf_counter() - start) * 1000
    logger.info(json.dumps({
        "event": "relay_response",
        "method": method.upper(),
        "url": target_url,
        "status": resp.status_code,
        "elapsed_ms": round(elapsed, 2)
    }))

    # --- Streaming (SSE) ---
    content_type = resp.headers.get("content-type", "")
    if "text/event-stream" in content_type:
        async def event_stream():
            async for chunk in resp.aiter_bytes():
                yield chunk
        return StreamingResponse(event_stream(), media_type="text/event-stream")

    # --- JSON responses ---
    if content_type.startswith("application/json"):
        try:
            return JSONResponse(resp.json(), status_code=resp.status_code)
        except Exception:
            pass

    # --- Fallback for non-JSON responses ---
    return JSONResponse(
        {
            "object": "proxy_response",
            "status": resp.status_code,
            "content_type": content_type,
            "body": getattr(resp, "text", "")[:1000],
        },
        status_code=resp.status_code,
    )


# ================================================================
# Graceful Shutdown Hook
# ================================================================
import atexit

@atexit.register
def on_shutdown():
    logger.info("🛑 Relay process exiting cleanly")
