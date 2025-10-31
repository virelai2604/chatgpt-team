# ==========================================================
# app/routes/responses.py — Ground Truth Responses Router
# ==========================================================
"""
Implements /v1/responses routes compatible with OpenAI's 2025.11 API.

Supports:
  • Non-streaming responses
  • Streaming (SSE) responses
  • Chain Wait orchestration
  • Dynamic Tool invocation under /v1/responses/tools/*
  • Unified image/video generation tools (formerly /v1/files/*/generations)
"""

import logging
import json
from typing import Any, Dict, AsyncGenerator
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse

from app.api.forward_openai import forward_openai_request
from app.api.tools_api import execute_tool

logger = logging.getLogger("responses")
router = APIRouter(prefix="/v1/responses", tags=["Responses"])


async def event_stream(generator: AsyncGenerator[str, None]) -> AsyncGenerator[bytes, None]:
    """Convert OpenAI-style async generator into byte SSE stream."""
    async for chunk in generator:
        if isinstance(chunk, (dict, list)):
            chunk = json.dumps(chunk)
        yield f"data: {chunk}\n\n".encode("utf-8")
    yield b"data: [DONE]\n\n"


@router.post("")
async def create_response(request: Request):
    """Forward a /v1/responses request to OpenAI (streaming or non-streaming)."""
    try:
        body = await request.json()
        headers = request.headers
        stream = headers.get("accept", "").lower() == "text/event-stream"
        logger.info(f"🌀 Incoming response request (stream={stream})")

        if stream:
            generator = await forward_openai_request("/v1/responses", body, stream=True)
            return StreamingResponse(event_stream(generator), media_type="text/event-stream")
        else:
            result = await forward_openai_request("/v1/responses", body, stream=False)
            return JSONResponse(result)

    except Exception as e:
        logger.exception(f"❌ Error handling /v1/responses: {e}")
        return JSONResponse({"error": str(e), "type": "relay_error"}, status_code=500)


@router.post("/chain/wait")
async def chain_wait_mode(request: Request):
    """Executes a series of model/tool steps sequentially."""
    try:
        payload = await request.json()
        steps = payload.get("steps", [])
        logger.info(f"🔗 Starting CHAIN_WAIT_MODE with {len(steps)} steps")

        results = []
        for step in steps:
            if "model" in step:
                res = await forward_openai_request("/v1/responses", step, stream=False)
                results.append(res)
            elif "tool" in step:
                tool = step["tool"]
                params = step.get("params", {})
                res = await execute_tool(tool, params)
                results.append(res)
            else:
                results.append({"error": "invalid_step", "details": step})

        return JSONResponse({"object": "chain_result", "steps": results})

    except Exception as e:
        logger.exception(f"❌ Chain wait error: {e}")
        return JSONResponse({"error": str(e), "type": "chain_wait_error"}, status_code=500)


@router.get("/tools")
async def list_tools():
    """Return available tools from the manifest."""
    try:
        from app.manifests.tools_manifest import TOOLS_MANIFEST
        return JSONResponse({"object": "tool.list", "data": TOOLS_MANIFEST})
    except Exception as e:
        logger.exception("⚠️ Failed to list tools")
        return JSONResponse({"error": str(e)}, status_code=500)


@router.post("/tools/{tool_name}")
async def invoke_tool(tool_name: str, request: Request):
    """Dynamically executes a registered tool."""
    try:
        params = await request.json()
        logger.info(f"🧠 Executing tool: {tool_name}")
        result = await execute_tool(tool_name, params)
        return JSONResponse(result)
    except Exception as e:
        logger.exception(f"❌ Tool '{tool_name}' failed: {e}")
        return JSONResponse({"detail": f"Tool '{tool_name}' failed: {e}"}, status_code=500)
