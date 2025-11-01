"""
passthrough_proxy.py — Ground Truth API v1.7
Fallback passthrough proxy to the official OpenAI API endpoint.
Supports JSON and streaming (SSE) passthrough with httpx >= 0.27.

This file ensures SDK 2.6.1 and FastAPI compatibility.
"""

import os
import httpx
from fastapi import APIRouter, Request, HTTPException, Response
from fastapi.responses import JSONResponse, StreamingResponse
from app.utils.logger import logger

router = APIRouter()

# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------

OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
TIMEOUT = float(os.getenv("PROXY_TIMEOUT", "180"))
DISABLE_PASSTHROUGH = os.getenv("DISABLE_PASSTHROUGH", "false").lower() == "true"


# --------------------------------------------------------------------------
# Core Passthrough Function
# --------------------------------------------------------------------------

async def _passthrough_request(method: str, path: str, request: Request) -> Response:
    """
    Generic request forwarder that mirrors OpenAI API behavior.
    Automatically handles JSON, binary, and SSE responses.
    """

    if DISABLE_PASSTHROUGH:
        raise HTTPException(status_code=403, detail="Passthrough disabled by configuration")

    target_url = f"{OPENAI_API_BASE}{path}"
    headers = {k: v for k, v in request.headers.items() if k.lower() not in {"host", "content-length"}}

    headers["Authorization"] = f"Bearer {OPENAI_API_KEY}"
    headers["User-Agent"] = "ChatGPT-Team-Relay/2025.11"
    headers.setdefault("OpenAI-Organization", os.getenv("OPENAI_ORG_ID", "default-org"))
    headers.setdefault("OpenAI-Beta", "true")

    try:
        body_bytes = await request.body()
    except Exception:
        body_bytes = b""

    logger.info(f"🔁 Passthrough {method.upper()} → {target_url}")

    # ----------------------------------------------------------------------
    # Modern httpx streaming style (>=0.27)
    # ----------------------------------------------------------------------
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        async with client.stream(
            method.upper(),
            target_url,
            headers=headers,
            content=body_bytes,
            follow_redirects=True,
        ) as response:

            # Streamed (SSE) passthrough
            if response.headers.get("content-type", "").startswith("text/event-stream"):
                async def event_stream():
                    async for chunk in response.aiter_bytes():
                        yield chunk

                return StreamingResponse(
                    event_stream(),
                    media_type="text/event-stream",
                    status_code=response.status_code,
                    headers={
                        "Cache-Control": "no-cache",
                        "X-Relay-Mode": "sse"
                    },
                )

            # JSON response passthrough
            try:
                data = await response.json()
                out = JSONResponse(status_code=response.status_code, content=data)
                for key in ["x-request-id", "openai-processing-ms", "openai-model"]:
                    if key in response.headers:
                        out.headers[key] = response.headers[key]
                return out
            except Exception:
                raw = await response.aread()
                return Response(
                    content=raw,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                )


# --------------------------------------------------------------------------
# Router Handler
# --------------------------------------------------------------------------

@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def passthrough(request: Request, path: str):
    """
    Catch-all route — forwards all unhandled requests to OpenAI.
    Prevents recursion into locally implemented /v1 routes.
    """

    if any(path.startswith(p) for p in [
        "v1/responses",
        "v1/files",
        "v1/conversations",
        "v1/vector_stores",
        "v1/realtime",
        "v1/embeddings"
    ]):
        return JSONResponse(
            status_code=404,
            content={"error": "Local route exists but not enabled or overridden."}
        )

    try:
        return await _passthrough_request(request.method, f"/{path}", request)
    except Exception as e:
        logger.error(f"Passthrough error: {e}")
        raise HTTPException(status_code=502, detail=str(e))
