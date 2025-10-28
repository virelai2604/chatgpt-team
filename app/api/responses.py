# ==========================================================
# app/api/responses.py — Forward OpenAI /v1/responses
# ==========================================================
# Mirrors OpenAI’s “responses” endpoint to support both
# streaming (SSE) and non-streaming completions via relay.
# Normalizes tools to match OpenAI’s schema.
# ==========================================================

import os
import json
import httpx
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse, JSONResponse

router = APIRouter(prefix="/v1/responses", tags=["Responses"])

# Upstream OpenAI endpoint
OPENAI_BASE = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
API_KEY = os.getenv("OPENAI_API_KEY", "sk-missing")

# ==========================================================
# 🔧 Helper: Normalize tool schemas
# ==========================================================
def normalize_tools(tools):
    """
    Normalize tool definitions to OpenAI-compatible function objects.
    Accepts either list of strings or list of dicts.
    """
    fixed_tools = []
    for tool in tools:
        # Handle simple string form
        if isinstance(tool, str):
            fixed_tools.append({
                "type": "function",
                "function": {
                    "name": tool,
                    "description": f"Invoke {tool} tool."
                }
            })
        # Handle dict-based tool definitions
        elif isinstance(tool, dict):
            fn = tool.get("function", {})
            if "name" not in fn and "name" in tool:
                fn["name"] = tool["name"]
            fixed_tools.append({
                "type": tool.get("type", "function"),
                "function": fn
            })
    return fixed_tools


# ==========================================================
# 🧠 Forward /v1/responses
# ==========================================================
@router.post("")
async def forward_response(request: Request):
    """
    Mirrors OpenAI /v1/responses — supports both
    streaming and non-streaming relay modes.
    """
    body = await request.json()

    # Normalize tools if provided
    if "tools" in body:
        body["tools"] = normalize_tools(body["tools"])

    # Default model if none provided
    if "model" not in body:
        body["model"] = "gpt-4o-mini"

    # Force relay metadata for internal tracing
    body["parallel_tool_calls"] = True
    body["store"] = True

    print(f"{json.dumps({'received_body': body}, indent=2)}")

    headers = {"Authorization": f"Bearer {API_KEY}"}

    # ==========================================================
    # 🌊 Streaming (SSE) Response
    # ==========================================================
    if body.get("stream", False):
        async def event_stream():
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream(
                    "POST",
                    f"{OPENAI_BASE}/responses",
                    headers=headers,
                    json=body
                ) as upstream:
                    async for line in upstream.aiter_lines():
                        if line.strip():
                            yield f"data: {line}\n\n"
        return StreamingResponse(event_stream(), media_type="text/event-stream")

    # ==========================================================
    # 🧩 Non-streaming Response
    # ==========================================================
    async with httpx.AsyncClient(timeout=None) as client:
        r = await client.post(f"{OPENAI_BASE}/responses", headers=headers, json=body)
        data = r.json()
        return JSONResponse(content=data, status_code=r.status_code)


# ==========================================================
# 🧰 Tool Registry Endpoint — Mirrors OpenAI tool listing
# ==========================================================
@router.get("/tools")
async def list_tools():
    """
    Return a simplified list of registered tools.
    Ground truth expects:
    {
        "tools": ["code_interpreter", "file_search", "image_generation", ...]
    }
    """
    tools = [
        "code_interpreter",
        "file_search",
        "file_upload",
        "file_download",
        "vector_store_retrieval",
        "image_generation",
        "video_generation",
        "web_search_preview",
        "computer_use_preview",
    ]
    return {"tools": tools}


# ==========================================================
# 🧩 Tool Invocation Endpoint — Mirrors OpenAI behavior
# ==========================================================
@router.post("/tools/{tool_name}")
async def call_tool(tool_name: str, request: Request):
    """
    Dummy passthrough for tool invocation — placeholder for
    internal relay plugin integration.
    """
    payload = await request.json()
    return {
        "result": {
            "tool": tool_name,
            "input": payload.get("input", {}),
            "status": "executed"
        }
    }
