# ==========================================================
#  app/api/forward.py — BIFL v2.3.3+ (Stable Streaming Edition)
#  Unified HTTP forwarder for OpenAI-compatible requests.
#  Handles:
#   • Full JSON responses
#   • StreamingResponse relay (NDJSON)
#   • Dynamic OpenAI-Beta header injection
#   • Trace ID logging & graceful stream shutdown
# ==========================================================

import os
import httpx
import uuid
import asyncio
import logging
from fastapi import Request
from fastapi.responses import StreamingResponse, JSONResponse
from httpx import StreamClosed
from app.utils.error_handler import error_response
from app.utils.db_logger import save_raw_request


# ──────────────────────────────────────────────
#  Configuration
# ──────────────────────────────────────────────
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_ORG_ID = os.getenv("OPENAI_ORG_ID", "")
DEBUG_MODE = os.getenv("DEBUG", "false").lower() == "true"
RELAY_TIMEOUT = int(os.getenv("RELAY_TIMEOUT", "120"))

logger = logging.getLogger("bifl.forward")
logging.basicConfig(
    level=logging.DEBUG if DEBUG_MODE else logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
)


# ──────────────────────────────────────────────
#  Helpers
# ──────────────────────────────────────────────
def _beta_headers(endpoint: str) -> dict:
    """Automatically attach the correct OpenAI-Beta header depending on endpoint."""
    if "responses" in endpoint:
        return {"OpenAI-Beta": "responses=v3"}
    if "videos" in endpoint:
        return {"OpenAI-Beta": "sora-2-pro=v3"}
    if "vector_stores" in endpoint:
        return {"OpenAI-Beta": "vector-stores=v2"}
    if "realtime" in endpoint:
        return {"OpenAI-Beta": "gpt-5-realtime=v1"}
    return {}


def _auth_headers(extra=None):
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
    }
    if OPENAI_ORG_ID:
        headers["OpenAI-Organization"] = OPENAI_ORG_ID
    if extra:
        headers.update(extra)
    return headers


async def _log_request_async(endpoint: str, body: bytes):
    """Log raw request body asynchronously to SQLite."""
    try:
        await asyncio.to_thread(save_raw_request, endpoint, body.decode("utf-8", "ignore"), "{}", "2.3.3")
    except Exception as e:
        logger.warning(f"[BIFL] Failed to log request: {e}")


# ──────────────────────────────────────────────
#  Main Forwarder
# ──────────────────────────────────────────────
async def forward_openai(request: Request, endpoint: str):
    """
    Forwards any /v1/* request to OpenAI API, preserving streaming and headers.
    """
    trace_id = str(uuid.uuid4())
    body = await request.body()

    # Build headers
    headers = {
        k.decode(): v.decode()
        for k, v in request.headers.raw
        if k.decode().lower() not in ["host", "authorization"]
    }
    headers.update(_auth_headers(_beta_headers(endpoint)))

    if DEBUG_MODE:
        logger.debug(f"[TRACE {trace_id}] → Forwarding {request.method} {endpoint}")

    # Log locally (fire-and-forget)
    asyncio.create_task(_log_request_async(endpoint, body))

    async with httpx.AsyncClient(timeout=RELAY_TIMEOUT) as client:
        try:
            async with client.stream(request.method, f"{OPENAI_BASE_URL}{endpoint}", headers=headers, content=body) as resp:
                # Non-2xx response
                if resp.status_code >= 400:
                    error_text = await resp.aread()
                    logger.warning(f"[BIFL] Proxy error {resp.status_code}: {error_text[:200]}")
                    return error_response(
                        "proxy_error",
                        error_text.decode(errors="ignore"),
                        resp.status_code,
                        {"trace_id": trace_id},
                    )

                # Streaming mode (Server-Sent Events / NDJSON)
                async def stream():
                    try:
                        async for chunk in resp.aiter_bytes():
                            yield chunk
                            # Give Starlette time to flush buffer
                            await asyncio.sleep(0)
                    except StreamClosed:
                        # Normal end-of-stream, do nothing
                        if DEBUG_MODE:
                            logger.debug(f"[TRACE {trace_id}] Stream closed cleanly.")
                        return
                    except Exception as e:
                        logger.warning(f"[TRACE {trace_id}] Stream aborted: {e}")
                        return

                # Detect if streaming
                content_type = resp.headers.get("content-type", "")
                if "stream" in content_type or "ndjson" in content_type:
                    return StreamingResponse(stream(), media_type=content_type)

                # Otherwise, return full JSON payload
                data = await resp.aread()
                try:
                    return JSONResponse(content=resp.json())
                except Exception:
                    # fallback if OpenAI returns raw bytes
                    return JSONResponse(
                        content={"raw": data.decode(errors="ignore")},
                        status_code=resp.status_code,
                    )

        except Exception as e:
            logger.error(f"[TRACE {trace_id}] Forwarding failed: {e}")
            return error_response("relay_exception", str(e), 502, {"trace_id": trace_id})
