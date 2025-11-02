# ================================================================
# forward_openai.py — Ground Truth Passthrough Proxy (v1.7)
# ================================================================
# Forwards all HTTP requests to OpenAI’s upstream API with:
#   • JSON + multipart/form-data support
#   • SSE (text/event-stream) streaming
#   • Full OpenAI SDK parity and error schema
#   • Automatic logging, latency metrics, and safe fallbacks
# ================================================================

import os
import time
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
# Header Utilities
# ================================================================
def _build_headers(incoming: Dict[str, str]) -> Dict[str, str]:
    """Clone and sanitize incoming headers, inject proper auth."""
    headers = dict(incoming)
    headers.pop("host", None)
    headers["Authorization"] = f"Bearer {OPENAI_API_KEY}"
    if OPENAI_ORG_ID:
        headers["OpenAI-Organization"] = OPENAI_ORG_ID
    return headers


# ================================================================
# Forwarder Core
# ================================================================
async def forward_to_openai(request: Request, path: str) -> Any:
    """
    Universal forwarder for all route modules.
    Automatically:
      • Handles JSON, multipart, and stream requests
      • Preserves OpenAI-style responses
      • Returns FastAPI JSONResponse or StreamingResponse
    """

    method = request.method.lower()
    headers = _build_headers(request.headers)

    # --- Normalize the upstream target URL ---
    base = OPENAI_API_BASE.rstrip("/")
    path = path.lstrip("/")

    # If the base already ends with '/v1' and path starts with 'v1',
    # remove the redundant prefix to avoid '.../v1/v1/...'
    if base.endswith("/v1") and path.startswith("v1/"):
        target_url = f"{base}/{path[3:].lstrip('/')}"
    else:
        target_url = f"{base}/{path}"

    logger.info(f"🔁 {method.upper()} {target_url}")

    # --- Prepare request body or form data ---
    ctype = headers.get("content-type", "").lower()
    body = None
    files = None

    if "multipart/form-data" in ctype:
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
        send_kwargs = {"content": body}

    start = time.perf_counter()

    async with httpx.AsyncClient(timeout=RELAY_TIMEOUT, follow_redirects=True) as client:
        try:
            resp = await client.request(method, target_url, headers=headers, **send_kwargs)
        except httpx.RequestError as e:
            logger.error(f"❌ Network error contacting OpenAI: {e}")
            return JSONResponse(
                {
                    "error": {
                        "message": f"Request failed: {e}",
                        "type": "network_error",
                        "param": None,
                        "code": "request_failed",
                    }
                },
                status_code=502,
            )

    elapsed = (time.perf_counter() - start) * 1000
    logger.info(f"✅ {resp.status_code} from OpenAI in {elapsed:.1f} ms")

    # --- Streaming Responses (SSE) ---
    content_type = resp.headers.get("content-type", "")
    if "text/event-stream" in content_type:
        async def event_stream():
            async for chunk in resp.aiter_bytes():
                yield chunk
        return StreamingResponse(event_stream(), media_type="text/event-stream")

    # --- JSON Responses ---
    if content_type.startswith("application/json"):
        try:
            return JSONResponse(resp.json(), status_code=resp.status_code)
        except Exception:
            pass

    # --- Non-JSON Fallback (binary, text, etc.) ---
    return JSONResponse(
        {
            "object": "proxy_response",
            "status": resp.status_code,
            "content_type": content_type,
            "body": getattr(resp, "text", "")[:2000],  # Truncate long payloads
        },
        status_code=resp.status_code,
    )
