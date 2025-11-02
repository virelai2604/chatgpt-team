# ================================================================
# forward_openai.py — Production-Grade Passthrough Proxy
# ================================================================
# Forwards all HTTP requests to OpenAI’s upstream API.
# Supports:
#   • JSON + multipart/form-data uploads
#   • SSE (text/event-stream) streaming
#   • Automatic logging + latency metrics
#   • Graceful fallback + error reporting
# ================================================================

import os
import time
import httpx
import logging
from typing import Optional, Dict, Any
from fastapi import Request
from fastapi.responses import StreamingResponse, JSONResponse

logger = logging.getLogger("relay")

OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_ORG_ID = os.getenv("OPENAI_ORG_ID")
RELAY_TIMEOUT = float(os.getenv("RELAY_TIMEOUT", 120))


def _build_headers(original: Dict[str, str]) -> Dict[str, str]:
    """Clone incoming headers, override auth + host."""
    headers = dict(original)
    headers["Authorization"] = f"Bearer {OPENAI_API_KEY}"
    headers["Host"] = "api.openai.com"
    if OPENAI_ORG_ID:
        headers["OpenAI-Organization"] = OPENAI_ORG_ID
    return headers


async def forward_to_openai(request: Request, path: str) -> Any:
    """
    Core forwarder used by all route modules.

    Automatically:
      • Detects multipart uploads
      • Handles SSE streams
      • Returns JSONResponse or StreamingResponse
    """
    method = request.method.lower()
    target_url = f"{OPENAI_API_BASE}/{path.lstrip('/')}"
    headers = _build_headers(request.headers)

    # --- Prepare body or form data ---
    content_type = headers.get("content-type", "")
    body = None
    files = None

    if "multipart/form-data" in content_type.lower():
        # Read multipart form manually
        form = await request.form()
        files = []
        data = {}
        for field, value in form.multi_items():
            if hasattr(value, "filename") and value.filename:
                files.append((field, (value.filename, value.file, value.content_type)))
            else:
                data[field] = value
        send_kwargs = {"data": data, "files": files}
    else:
        # Raw body (JSON or plain)
        body = await request.body()
        send_kwargs = {"content": body}

    start_time = time.perf_counter()

    async with httpx.AsyncClient(timeout=RELAY_TIMEOUT, follow_redirects=True) as client:
        try:
            logger.info(f"🔁 {method.upper()} {target_url}")
            response = await client.request(method, target_url, headers=headers, **send_kwargs)
        except httpx.RequestError as e:
            logger.error(f"❌ Network error contacting OpenAI: {e}")
            return JSONResponse(
                {"object": "error", "message": f"Request failed: {e}", "path": path},
                status_code=502,
            )

    elapsed = (time.perf_counter() - start_time) * 1000
    logger.info(f"✅ {response.status_code} from OpenAI in {elapsed:.1f} ms")

    # --- Handle Streaming Responses (SSE) ---
    content_type = response.headers.get("content-type", "")
    if "text/event-stream" in content_type:
        def event_generator():
            for chunk in response.iter_bytes():
                yield chunk
        return StreamingResponse(event_generator(), media_type="text/event-stream")

    # --- Normal JSON or binary responses ---
    try:
        return JSONResponse(response.json(), status_code=response.status_code)
    except Exception:
        # Non-JSON responses (e.g., file downloads)
        return JSONResponse(
            {
                "object": "proxy_response",
                "status": response.status_code,
                "content_type": content_type,
                "body": response.text[:2000],  # truncate for safety
            },
            status_code=response.status_code,
        )
