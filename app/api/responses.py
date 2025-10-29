# ==========================================================
# 🚀 ChatGPT Team Relay — /v1/responses API (Ground Truth)
# ----------------------------------------------------------
# Full alignment with OpenAI 2025 schema for /v1/responses.
# Automatically normalizes incoming payloads from tests or
# external clients for full compatibility.
# ==========================================================

import os
import json
import httpx
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse

router = APIRouter(prefix="/v1/responses", tags=["Responses"])

# ==========================================================
# 🌍 Environment Configuration
# ==========================================================

OPENAI_BASE = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
API_KEY = os.getenv("OPENAI_API_KEY", "sk-missing")

# ==========================================================
# 🧩 Helpers
# ==========================================================

def normalize_tools(tools):
    """
    Normalize tool structures to match OpenAI's expected schema.
    Accepts either list of names or detailed dicts.
    """
    normalized = []
    for tool in tools:
        if isinstance(tool, str):
            normalized.append({
                "type": "function",
                "function": {
                    "name": tool,
                    "description": f"Invoke {tool} tool."
                }
            })
        elif isinstance(tool, dict):
            fn = tool.get("function", {})
            if "name" not in fn and "name" in tool:
                fn["name"] = tool["name"]
            normalized.append({
                "type": tool.get("type", "function"),
                "function": fn
            })
    return normalized


def normalize_payload(body: dict) -> dict:
    """
    Adjust test and legacy relay payloads into the current
    OpenAI /v1/responses contract.
    """
    # Convert test field "response_format" → "response.format"
    if "response_format" in body:
        fmt = body.pop("response_format")
        body["response"] = {"format": fmt}

    # Ensure content types use "input_text"
    if "input" in body and isinstance(body["input"], list):
        for msg in body["input"]:
            if "content" in msg:
                for item in msg["content"]:
                    if item.get("type") == "text":
                        item["type"] = "input_text"

    # Default response format
    if "response" not in body:
        body["response"] = {"format": "text"}

    # Default model if missing
    if "model" not in body:
        body["model"] = "gpt-4o-mini"

    return body


# ==========================================================
# 🧠 /v1/responses — Core Relay Endpoint
# ==========================================================

@router.post("")
async def forward_response(request: Request):
    """
    Forwards compliant requests to OpenAI’s /v1/responses endpoint.
    Supports both streaming and non-stream modes.
    """
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    # Normalize schema
    body = normalize_payload(body)

    # Normalize tool list if present
    if "tools" in body:
        body["tools"] = normalize_tools(body["tools"])

    headers = {"Authorization": f"Bearer {API_KEY}"}

    # ======================================================
    # 🌊 Streaming Mode (SSE)
    # ======================================================
    if body.get("stream", False):
        async def sse_stream():
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream(
                    "POST", f"{OPENAI_BASE}/responses", headers=headers, json=body
                ) as upstream:
                    async for line in upstream.aiter_lines():
                        if line.strip():
                            yield f"data: {line}\n\n"
        return StreamingResponse(sse_stream(), media_type="text/event-stream")

    # ======================================================
    # 🧩 Non-Streaming Mode
    # ======================================================
    async with httpx.AsyncClient(timeout=None) as client:
        resp = await client.post(f"{OPENAI_BASE}/responses", headers=headers, json=body)

    if resp.status_code >= 400:
        return JSONResponse(
            {"error": {"status": resp.status_code, "message": resp.text}},
            status_code=resp.status_code
        )

    return JSONResponse(content=resp.json(), status_code=resp.status_code)


# ==========================================================
# 🧰 Tool Registry Endpoint
# ==========================================================

@router.get("/tools")
async def list_tools():
    """
    Lists all registered tools available to the relay.
    Schema mirrors OpenAI’s tool discovery pattern.
    """
    tools = [
        "code_interpreter",
        "file_search",
        "file_upload",
        "file_download",
        "vector_store_retrieval",
        "image_generation",
        "video_generation",
        "web_search",
        "computer_use",
    ]
    return {
        "object": "list",
        "tools": tools,
        "count": len(tools),
        "registry_version": "1.0"
    }


# ==========================================================
# 🔧 Tool Invocation Stub
# ==========================================================

@router.post("/tools/{tool_name}")
async def invoke_tool(tool_name: str, request: Request):
    """
    Echo endpoint for verifying tool invocation schema.
    """
    data = await request.json()
    return {
        "tool_invoked": tool_name,
        "received": data,
        "status": "accepted"
    }


# ==========================================================
# ✅ End of responses.py
# ==========================================================
