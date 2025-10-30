# ==========================================================
# app/routes/responses.py — Ground Truth Responses API (2025.10)
# ==========================================================
"""
Implements the OpenAI-compatible /v1/responses endpoint.

Includes:
  • /v1/responses (non-stream and stream modes)
  • /v1/responses/tools/* (dynamic tool execution)
  • Chain Wait orchestration for multi-step tool usage
"""

import logging
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from typing import Dict, Any
import asyncio
import json
import os

from app.routes.tools import execute_tool_from_manifest, list_registered_tools
from app.api.forward_openai import forward_openai_request

# Router
router = APIRouter(prefix="/v1/responses", tags=["Responses"])
logger = logging.getLogger("responses")

# Environment configuration
CHAIN_WAIT_MODE = os.getenv("CHAIN_WAIT_MODE", "false").lower() == "true"
ENABLE_STREAM = os.getenv("ENABLE_STREAM", "true").lower() == "true"


# ----------------------------------------------------------
# POST /v1/responses — Main Responses Endpoint
# ----------------------------------------------------------
@router.post("")
async def create_response(request: Request):
    """Unified Responses endpoint with optional streaming."""
    headers = request.headers
    accept = headers.get("accept", "")
    stream_mode = "text/event-stream" in accept or ENABLE_STREAM

    try:
        body = await request.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}")

    model = body.get("model")
    input_data = body.get("input")

    if not model:
        raise HTTPException(status_code=400, detail="Missing 'model' field in request body.")

    if stream_mode:
        async def event_stream():
            logger.info(f"🌀 Streaming response for model: {model}")
            async for chunk in forward_openai_request(
                endpoint="/v1/responses",
                json_body=body,
                stream=True,
            ):
                yield f"data: {json.dumps(chunk)}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    # Non-streaming mode
    result = await forward_openai_request(
        endpoint="/v1/responses",
        json_body=body,
        stream=False,
    )
    return JSONResponse(result)


# ----------------------------------------------------------
# POST /v1/responses/tools/{tool_name} — Dynamic Tool Executor
# ----------------------------------------------------------
@router.post("/tools/{tool_name}")
async def execute_tool(tool_name: str, request: Request):
    """
    Dynamically executes a registered tool defined in tools_manifest.json.

    Example:
        POST /v1/responses/tools/image_generation
        { "prompt": "a futuristic city skyline" }
    """
    try:
        params = await request.json()
    except Exception:
        params = {}

    # Confirm tool is registered
    registry = list_registered_tools()
    tool_entry = next((t for t in registry if t["name"] == tool_name), None)
    if not tool_entry:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found in manifest registry.")

    logger.info(f"🧠 Executing tool: {tool_name} with params: {params}")

    try:
        result = await execute_tool_from_manifest(tool_name, params)
        return JSONResponse({"tool": tool_name, "result": result})
    except Exception as e:
        logger.error(f"❌ Tool '{tool_name}' failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ----------------------------------------------------------
# GET /v1/responses/tools — Tool Registry Listing
# ----------------------------------------------------------
@router.get("/tools")
async def list_tools():
    """List all dynamically registered tools."""
    tools = list_registered_tools()
    return {"count": len(tools), "tools": tools}


# ----------------------------------------------------------
# CHAIN_WAIT_MODE (Optional: Orchestrated Tool Flow)
# ----------------------------------------------------------
@router.post("/chain/wait")
async def chain_wait_mode(request: Request):
    """
    Demonstrates a chain-wait orchestration pattern:
      - Accepts a sequence of steps (model + tool)
      - Waits for each to complete before continuing
    """
    if not CHAIN_WAIT_MODE:
        raise HTTPException(status_code=400, detail="CHAIN_WAIT_MODE is disabled.")

    body = await request.json()
    steps = body.get("steps", [])
    if not steps:
        raise HTTPException(status_code=400, detail="No steps provided.")

    outputs = []
    for step in steps:
        model = step.get("model")
        input_data = step.get("input")
        tool = step.get("tool")
        params = step.get("params", {})

        logger.info(f"⏳ Executing chain step: {model or tool}")
        if tool:
            result = await execute_tool_from_manifest(tool, params)
            outputs.append({"tool": tool, "result": result})
        elif model:
            result = await forward_openai_request(
                endpoint="/v1/responses",
                json_body={"model": model, "input": input_data},
                stream=False,
            )
            outputs.append({"model": model, "response": result})
        else:
            outputs.append({"error": "Invalid step entry"})

    return JSONResponse({"steps": outputs})
