# ============================================================
# app/api/responses.py — ChatGPT Team Relay (v2025 Final Fix)
# ============================================================
# Implements /v1/responses with OpenAI-compatible structure.
# Ensures GPT-5 tool schema compliance by enforcing both
# `tools[n].name` and `tools[n].function.name` fields.
# Supports streaming, dynamic tool discovery, and function calls.

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


# -------------------------------------------------------------
# 🌍 Environment setup
# -------------------------------------------------------------
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

router = APIRouter(prefix="/v1", tags=["Responses"])


# -------------------------------------------------------------
# ⚙️ Streaming helper
# -------------------------------------------------------------
async def _stream_response(upstream):
    """Stream OpenAI's chunked SSE output directly to the client."""
    async def _iter():
        async for chunk in upstream.aiter_bytes():
            if chunk:
                yield chunk
    headers = {
        k: v
        for k, v in upstream.headers.items()
        if k.lower() not in ("transfer-encoding", "content-length")
    }
    return StreamingResponse(_iter(), status_code=upstream.status_code, headers=headers)


# -------------------------------------------------------------
# 🧠 Core endpoint: POST /v1/responses
# -------------------------------------------------------------
@router.post("/responses")
async def create_response(request: Request):
    """
    Main relay handler for OpenAI /v1/responses endpoint.
    Supports streaming, dynamic tool injection, and function calling.
    """
    try:
        body = await request.json()
    except Exception:
        body = {}

    model = body.get("model", "gpt-5")
    stream = body.get("stream", False)
    tools = body.get("tools", [])

    # ---------------------------------------------------------
    # ✅ Inject local tools if not provided
    # ---------------------------------------------------------
    local_tools = list_local_tools()
    if not tools and local_tools:
        body["tools"] = local_tools
    else:
        body.pop("tools", None)

    # ---------------------------------------------------------
    # 🔧 Normalize tools to OpenAI schema
    # ---------------------------------------------------------
    if "tools" in body:
        fixed_tools = []
        for tool in body["tools"]:
            # Ensure all have type='function' and top-level name
            if "function" not in tool and "name" in tool:
                fn = {k: tool[k] for k in ("name", "description", "parameters") if k in tool}
                fixed_tools.append({
                    "type": "function",
                    "name": fn["name"],       # ✅ Top-level name required by OpenAI schema
                    "function": fn
                })
            else:
                fn = tool.get("function")
                if isinstance(fn, dict) and "name" in fn:
                    fixed_tools.append({
                        "type": "function",
                        "name": fn["name"],   # ✅ Add top-level name
                        "function": fn
                    })
        body["tools"] = fixed_tools

    # ---------------------------------------------------------
    # 🧩 Diagnostic logging (optional)
    # ---------------------------------------------------------
    print("\n=== [Relay → OpenAI] Final request body ===")
    print(json.dumps(body, indent=2))
    print("===========================================\n")

    # ---------------------------------------------------------
    # 🔑 Auth headers
    # ---------------------------------------------------------
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
        "X-Relay-Source": "chatgpt-team-relay",
    }

    print(f"[Relay Auth Check] Key loaded: {'✅ yes' if OPENAI_API_KEY else '❌ missing'}")
    url = f"{OPENAI_BASE_URL}/v1/responses"

    # ---------------------------------------------------------
    # 🚀 Forward request to OpenAI
    # ---------------------------------------------------------
    async with httpx.AsyncClient(timeout=None) as client:
        if stream:
            async with client.stream("POST", url, headers=headers, json=body) as upstream:
                return await _stream_response(upstream)
        else:
            response = await client.post(url, headers=headers, json=body)

    # ---------------------------------------------------------
    # 🔄 Handle function calls (tool invocations)
    # ---------------------------------------------------------
    try:
        data = response.json()
    except Exception:
        return JSONResponse(status_code=500, content={"error": "Invalid JSON from upstream"})

    if isinstance(data, dict) and "tool_calls" in data:
        tool_outputs = []
        for call in data["tool_calls"]:
            tool_name = call.get("name")
            tool_input = call.get("input", {})
            try:
                result = await run_tool(tool_name, tool_input)
                tool_outputs.append({"tool_name": tool_name, "result": result})
            except Exception as e:
                tool_outputs.append({"tool_name": tool_name, "error": str(e)})
        data["tool_outputs"] = tool_outputs

    # ---------------------------------------------------------
    # 🧾 Asynchronous logging
    # ---------------------------------------------------------
    try:
        await log_event("/v1/responses", response.status_code, f"model={model}")
    except Exception:
        pass

    return JSONResponse(status_code=response.status_code, content=data)


# -------------------------------------------------------------
# 🧰 /v1/responses/tools — list all available tools
# -------------------------------------------------------------
@router.get("/responses/tools")
async def list_tools():
    """Return all dynamically discovered tools in OpenAI-compatible schema."""
    tools = list_local_tools()
    return JSONResponse({"object": "list", "data": tools})


# -------------------------------------------------------------
# 🧩 /v1/responses/tools/{tool_name} — manual tool invocation
# -------------------------------------------------------------
@router.post("/responses/tools/{tool_name}")
async def call_tool(tool_name: str, request: Request):
    """Invoke a registered tool directly (without model mediation)."""
    payload = await request.json()
    result = await run_tool(tool_name, payload)
    return JSONResponse(result)
