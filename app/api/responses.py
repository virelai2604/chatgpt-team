# ============================================================
# app/api/responses.py — Relay v2025-10 (Fix #2 Ground Truth)
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
    """Pipe OpenAI streaming chunks to client."""
    async def _iter():
        async for chunk in upstream.aiter_bytes():
            if chunk:
                yield chunk
    headers = {k: v for k, v in upstream.headers.items() if k.lower() not in ("transfer-encoding", "content-length")}
    return StreamingResponse(_iter(), status_code=upstream.status_code, headers=headers)


# -------------------------------------------------------------
# 🧠 Core endpoint
# -------------------------------------------------------------
@router.post("/responses")
async def create_response(request: Request):
    """Relay for POST /v1/responses (GPT-5, streaming, and tools)."""
    try:
        body = await request.json()
    except Exception:
        body = {}

    model = body.get("model", "gpt-5")
    stream = body.get("stream", False)
    tools = body.get("tools", [])

    # ---------------------------------------------------------
    # ✅ Ground-truth tool packaging
    # ---------------------------------------------------------
    local_tools = list_local_tools()
    normalized_tools = []
    for t in local_tools:
        if not isinstance(t, dict):
            continue
        fn = t.get("function", {})
        if not isinstance(fn, dict):
            continue
        name = fn.get("name")
        params = fn.get("parameters")
        if name and isinstance(params, dict):
            normalized_tools.append({
                "type": t.get("type", "function"),
                "function": {
                    "name": name,
                    "description": fn.get("description", ""),
                    "parameters": params
                }
            })

    if not tools and normalized_tools:
        body["tools"] = normalized_tools
    else:
        body.pop("tools", None)

    # ---------------------------------------------------------
    # 🔑 Auth + headers
    # ---------------------------------------------------------
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
        "X-Relay-Source": "chatgpt-team-relay",
    }

    print(f"[Relay Auth Check] Key loaded: {'✅ yes' if OPENAI_API_KEY else '❌ missing'}")
    url = f"{OPENAI_BASE_URL}/v1/responses"

    # ---------------------------------------------------------
    # 🚀 Forward request
    # ---------------------------------------------------------
    async with httpx.AsyncClient(timeout=None) as client:
        if stream:
            async with client.stream("POST", url, headers=headers, json=body) as upstream:
                return await _stream_response(upstream)
        else:
            response = await client.post(url, headers=headers, json=body)

    # ---------------------------------------------------------
    # 🔄 Handle tool calls
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
    # 🧾 Non-blocking event log
    # ---------------------------------------------------------
    try:
        await log_event("/v1/responses", response.status_code, f"model={model}")
    except Exception:
        pass

    return JSONResponse(status_code=response.status_code, content=data)


# -------------------------------------------------------------
# 🧰 Tool listing + manual calls
# -------------------------------------------------------------
@router.get("/responses/tools")
async def list_tools():
    tools = list_local_tools()
    return JSONResponse({"object": "list", "data": tools})


@router.post("/responses/tools/{tool_name}")
async def call_tool(tool_name: str, request: Request):
    payload = await request.json()
    result = await run_tool(tool_name, payload)
    return JSONResponse(result)
