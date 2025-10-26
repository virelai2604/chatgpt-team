# ==========================================================
#  app/routes/responses.py — BIFL v2.3.3-p2
# ==========================================================
#  Unified /v1/responses route for standard, stream, and realtime
#  - Standard responses → JSONResponse
#  - stream:true → StreamingResponse (NDJSON)
#  - gpt-5-realtime → proxy to realtime session (future support)
# ==========================================================

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse
from app.api.forward import forward_openai
from app.utils.error_handler import error_response
from app.utils.db_logger import save_raw_request
import asyncio
import json
import uuid
import os
import logging

router = APIRouter(prefix="/v1", tags=["Responses"])
logger = logging.getLogger("bifl.responses")

# ──────────────────────────────────────────────
#  Unified /v1/responses endpoint
# ──────────────────────────────────────────────
@router.post("/responses")
async def create_response(request: Request):
    trace_id = str(uuid.uuid4())

    try:
        body = await request.json()
    except Exception:
        return error_response(
            "invalid_json", "Request body is not valid JSON", 400, {"trace_id": trace_id}
        )

    model = body.get("model")
    stream = body.get("stream", False)

    # Log raw request asynchronously
    asyncio.create_task(
        asyncio.to_thread(
            save_raw_request,
            "/v1/responses",
            json.dumps(body),
            "{}",
            "2.3.3-p2"
        )
    )

    # Detect realtime models (e.g., gpt-5-realtime)
    if model and "realtime" in model.lower():
        logger.info(f"[TRACE {trace_id}] Upgrading to realtime session for {model}")
        return JSONResponse(
            content={
                "status": "pending",
                "note": f"Realtime model {model} requires WebSocket (not REST).",
                "trace_id": trace_id,
            },
            status_code=426,  # Upgrade Required
        )

    # Handle streaming mode
    if stream:
        logger.info(f"[TRACE {trace_id}] → Stream mode active for {model}")

        async def stream_forward():
            async for chunk in await forward_openai(request, "/v1/responses"):
                yield chunk

        return StreamingResponse(
            stream_forward(),
            media_type="application/x-ndjson",
        )

    # Standard (non-stream) case
    logger.info(f"[TRACE {trace_id}] → Standard mode for {model}")
    result = await forward_openai(request, "/v1/responses")

    # Ensure pretty JSON output for PowerShell Invoke-RestMethod
    if isinstance(result, JSONResponse):
        result.media_type = "application/json"
    return result

# ──────────────────────────────────────────────
#  Simple tool listing endpoint
# ──────────────────────────────────────────────
@router.get("/tools/list")
async def list_tools():
    """Return available relay-side tools."""
    tools = [
        {"name": "embeddings", "endpoint": "/v1/embeddings"},
        {"name": "moderations", "endpoint": "/v1/moderations"},
        {"name": "files", "endpoint": "/v1/files"},
        {"name": "vector_stores", "endpoint": "/v1/vector_stores"},
        {"name": "videos", "endpoint": "/v1/videos"},
    ]
    return JSONResponse(content={"tools": tools, "version": "2.3.3-p2"})
