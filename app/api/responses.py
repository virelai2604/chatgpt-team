# ==========================================================
# app/api/responses.py — Relay v2025-10 Ground Truth Orchestrator
# ==========================================================
# This module defines the /v1/responses endpoint, which acts as the
# ChatGPT “brain.” It coordinates requests to models, handles tool calls,
# and manages streaming back to the client.
# ==========================================================

import json
import asyncio
import httpx
from fastapi import APIRouter, Request, Response
from fastapi.responses import StreamingResponse, JSONResponse
from app.api.forward_openai import OPENAI_BASE_URL
from app.api.tools_api import list_local_tools, run_tool
from app.utils.db_logger import log_event

router = APIRouter(prefix="/v1", tags=["Responses"])


# ----------------------------------------------------------
# ⚙️ Stream handler utility
# ----------------------------------------------------------
async def _stream_response(upstream):
    """Stream chunks from an upstream httpx.AsyncClient response."""
    async def stream_iter():
        async for chunk in upstream.aiter_bytes():
            if chunk:
                yield chunk
    # Filter headers to avoid FastAPI conflict
    headers = {
        k: v for k, v in upstream.headers.items()
        if k.lower() not in ("transfer-encoding", "content-length")
    }
    return StreamingResponse(stream_iter(), status_code=upstream.status_code, headers=headers)


# ----------------------------------------------------------
# 🧠 Core Orchestration Endpoint
# ----------------------------------------------------------
@router.post("/responses")
async def create_response(request: Request):
    """
    Main ChatGPT relay endpoint.
    - Forwards user input to OpenAI /v1/responses
    - Handles local tool invocation
    - Supports both streaming and non-streaming responses
    """
    body = await request.json()

    # Default behavior
    stream = body.get("stream", False)
    model = body.get("model", "gpt-5")
    tools = body.get("tools", [])
    messages = body.get("messages", [])

    # Auto-load available local tools
    local_tools = list_local_tools()

    # Merge tool manifest with provided tools (if any)
    if not tools:
        body["tools"] = local_tools

    # Inject headers for OpenAI-beta or GPT-5 if necessary
    headers = {
        "Authorization": request.headers.get("Authorization", ""),
        "Content-Type": "application/json",
        "X-Relay-Source": "chatgpt-team-relay",
    }

    # Upstream OpenAI Responses endpoint
    url = f"{OPENAI_BASE_URL}/v1/responses"

    async with httpx.AsyncClient(timeout=None) as client:
        if stream:
            upstream = await client.stream("POST", url, headers=headers, json=body)
            return await _stream_response(upstream)
        else:
            response = await client.post(url, headers=headers, json=body)
            data = response.json()

    # ------------------------------------------------------
    # 🧩 Tool Invocation (local tools)
    # ------------------------------------------------------
    # The OpenAI /v1/responses API may return tool calls.
    # If tools are declared locally, run them here.
    if isinstance(data, dict) and "tool_calls" in data:
        tool_outputs = []
        for tool_call in data["tool_calls"]:
            tool_name = tool_call.get("name")
            tool_input = tool_call.get("input", {})
            result = await run_tool(tool_name, tool_input)
            tool_outputs.append({
                "tool_name": tool_name,
                "result": result
            })
        data["tool_outputs"] = tool_outputs

    try:
        await log_event("/v1/responses", 200, f"model={model}")
    except Exception:
        pass

    return JSONResponse(data)


# ----------------------------------------------------------
# 🧰 List Available Tools
# ----------------------------------------------------------
@router.get("/responses/tools")
async def list_tools():
    """List all available local tools known to the relay."""
    tools = list_local_tools()
    return JSONResponse({"object": "list", "data": tools})


# ----------------------------------------------------------
# 🧩 Tool Invocation API
# ----------------------------------------------------------
@router.post("/responses/tools/{tool_name}")
async def call_tool(tool_name: str, request: Request):
    """
    Manually call a registered tool via API.
    Used internally by /v1/responses orchestration.
    """
    payload = await request.json()
    result = await run_tool(tool_name, payload)
    return JSONResponse(result)
