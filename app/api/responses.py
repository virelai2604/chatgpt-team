# ============================================================
# app/api/responses.py — Relay v2025-10 (Ground Truth Alignment)
# ============================================================

import os
import json
import httpx
import asyncio
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse, JSONResponse
from dotenv import load_dotenv

from app.api.tools_api import list_local_tools, run_tool
from app.api.forward_openai import OPENAI_BASE_URL
from app.utils.db_logger import log_event

# ---------------------------------------------------------------------
# 🌍 Load environment and constants
# ---------------------------------------------------------------------
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

router = APIRouter(prefix="/v1", tags=["Responses"])


# ---------------------------------------------------------------------
# ⚙️ Stream handler
# ---------------------------------------------------------------------
async def _stream_response(upstream):
    """Stream chunks from an upstream httpx.AsyncClient response."""
    async def stream_iter():
        async for chunk in upstream.aiter_bytes():
            if chunk:
                yield chunk

    headers = {
        k: v for k, v in upstream.headers.items()
        if k.lower() not in ("transfer-encoding", "content-length")
    }

    return StreamingResponse(stream_iter(), status_code=upstream.status_code, headers=headers)


# ---------------------------------------------------------------------
# 🧠 Main /v1/responses Endpoint
# ---------------------------------------------------------------------
@router.post("/responses")
async def create_response(request: Request):
    """
    Mirrors POST /v1/responses from the OpenAI API.
    Supports GPT-5, streaming, and tool execution.
    """
    try:
        body = await request.json()
    except Exception:
        body = {}

    # Model & streaming defaults
    model = body.get("model", "gpt-5")
    stream = body.get("stream", False)
    tools = body.get("tools", [])
    input_data = body.get("input", "")

    # -----------------------------------------------------------------
    # ✅ Auto-inject local tools safely
    # -----------------------------------------------------------------
    local_tools = list_local_tools()
    valid_tools = []
    for t in local_tools:
        if (
            isinstance(t, dict)
            and t.get("type") == "function"
            and isinstance(t.get("function"), dict)
            and "name" in t["function"]
            and "parameters" in t["function"]
        ):
            valid_tools.append(t)

    # Inject only if tools missing and valid tools exist
    if not tools and valid_tools:
        body["tools"] = valid_tools
    else:
        # Prevent malformed tools array from triggering OpenAI validation
        body.pop("tools", None)

    # -----------------------------------------------------------------
    # 🔑 Prepare headers with real API key
    # -----------------------------------------------------------------
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
        "X-Relay-Source": "chatgpt-team-relay",
    }

    print(f"[Relay Auth Check] Key loaded: {'✅ yes' if OPENAI_API_KEY else '❌ missing'}")

    url = f"{OPENAI_BASE_URL}/v1/responses"

    # -----------------------------------------------------------------
    # 🚀 Forward to OpenAI
    # -----------------------------------------------------------------
    async with httpx.AsyncClient(timeout=None) as client:
        if stream:
            async with client.stream("POST", url, headers=headers, json=body) as upstream:
                return await _stream_response(upstream)
        else:
            response = await client.post(url, headers=headers, json=body)

    # -----------------------------------------------------------------
    # 🧩 Tool execution (local tools)
    # -----------------------------------------------------------------
    try:
        data = response.json()
    except Exception:
        return JSONResponse(status_code=500, content={"error": "Invalid JSON from upstream"})

    if isinstance(data, dict) and "tool_calls" in data:
        tool_outputs = []
        for tool_call in data["tool_calls"]:
            tool_name = tool_call.get("name")
            tool_input = tool_call.get("input", {})
            try:
                result = await run_tool(tool_name, tool_input)
                tool_outputs.append({"tool_name": tool_name, "result": result})
            except Exception as e:
                tool_outputs.append({"tool_name": tool_name, "error": str(e)})
        data["tool_outputs"] = tool_outputs

    # -----------------------------------------------------------------
    # 🧾 Logging (non-blocking)
    # -----------------------------------------------------------------
    try:
        await log_event("/v1/responses", response.status_code, f"model={model}")
    except Exception:
        pass

    # Return upstream data directly
    return JSONResponse(status_code=response.status_code, content=data)


# ---------------------------------------------------------------------
# 🧰 List Tools for /v1/responses/tools
# ---------------------------------------------------------------------
@router.get("/responses/tools")
async def list_tools():
    """List all available local tools known to the relay."""
    tools = list_local_tools()
    return JSONResponse({"object": "list", "data": tools})


# ---------------------------------------------------------------------
# 🧩 Manual Tool Invocation (for testing)
# ---------------------------------------------------------------------
@router.post("/responses/tools/{tool_name}")
async def call_tool(tool_name: str, request: Request):
    """Manually call a registered tool via API."""
    payload = await request.json()
    result = await run_tool(tool_name, payload)
    return JSONResponse(result)
