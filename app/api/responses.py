# ==========================================================
# app/api/responses.py — Relay v2025-10 Ground Truth Orchestrator
# ==========================================================
import os
import json
import asyncio
import httpx
from fastapi import APIRouter, Request, Response
from fastapi.responses import StreamingResponse, JSONResponse
from dotenv import load_dotenv
from app.api.forward_openai import OPENAI_BASE_URL
from app.api.tools_api import list_local_tools, run_tool
from app.utils.db_logger import log_event

# ✅ Ensure .env is loaded before fetching keys
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

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
    Forwards user input to OpenAI /v1/responses.
    Supports streaming and tool orchestration.
    """
    body = await request.json()

    stream = body.get("stream", False)
    model = body.get("model", "gpt-5")
    tools = body.get("tools", [])
    messages = body.get("messages", [])

    local_tools = list_local_tools()
    if not tools:
        body["tools"] = local_tools

    # ✅ Inject your real API key instead of "dummy"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
        "X-Relay-Source": "chatgpt-team-relay",
    }

    print(f"[Relay Auth Check] Key loaded: {'✅ yes' if OPENAI_API_KEY else '❌ missing'}")

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
    if isinstance(data, dict) and "tool_calls" in data:
        tool_outputs = []
        for tool_call in data["tool_calls"]:
            tool_name = tool_call.get("name")
            tool_input = tool_call.get("input", {})
            result = await run_tool(tool_name, tool_input)
            tool_outputs.append({"tool_name": tool_name, "result": result})
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
    """Manually call a registered tool via API."""
    payload = await request.json()
    result = await run_tool(tool_name, payload)
    return JSONResponse(result)
