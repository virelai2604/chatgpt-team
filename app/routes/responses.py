# ================================================================
# responses.py — Hybrid Responses + Tool Invocation Relay
# ================================================================
# Compatible with OpenAI SDK v2.6.1 and ChatGPT Actions.
# Supports both passthrough to OpenAI and internal tool execution.
# ================================================================

import json
import logging
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse
from app.api.forward_openai import forward_to_openai
from app.tools import (
    file_search,
    file_upload,
    image_generation,
    video_generation,
    vector_store_retrieval,
    web_search,
    computer_use,
    code_interpreter,
)

logger = logging.getLogger("relay")

router = APIRouter(tags=["responses"])

# Alias router for /responses (non-versioned)
responses_router = APIRouter(tags=["responses"])

# Mapping of tool names to internal handlers
TOOL_MAP = {
    "file_search": file_search,
    "file_upload": file_upload,
    "image_generation": image_generation,
    "video_generation": video_generation,
    "vector_store_retrieval": vector_store_retrieval,
    "web_search": web_search,
    "computer_use": computer_use,
    "code_interpreter": code_interpreter,
}


async def handle_tool_invocations(body: dict):
    """Executes internal tools listed in a Responses request."""
    results = []
    for tool in body.get("tools", []):
        tool_type = tool.get("type")
        tool_args = tool.get("args", {})
        handler = TOOL_MAP.get(tool_type)

        if not handler:
            results.append({
                "tool": tool_type,
                "status": "error",
                "output": {"message": f"Unknown tool: {tool_type}"}
            })
            continue

        try:
            # All tools implement `run(args: dict)` → dict output
            output = handler.run(tool_args)
            results.append({"tool": tool_type, "status": "success", "output": output})
        except Exception as e:
            results.append({"tool": tool_type, "status": "error", "output": {"error": str(e)}})
    return results


@router.post("/v1/responses")
async def create_response(request: Request):
    """Primary endpoint for generating responses with tool integration."""
    body = await request.json()
    tool_outputs = []

    # Handle tool invocations (local)
    if "tools" in body:
        tool_outputs = await handle_tool_invocations(body)

    # Forward to OpenAI if passthrough is desired
    resp = await forward_to_openai(request, "/v1/responses")
    try:
        json_body = resp.json()
    except Exception:
        json_body = {"object": "response", "status": "error", "message": resp.text}

    # Merge results
    json_body["tool_outputs"] = tool_outputs
    return JSONResponse(json_body, status_code=resp.status_code)


@router.post("/v1/responses:stream")
async def stream_response(request: Request):
    """Simulates streamed responses (SSE passthrough)."""
    resp = await forward_to_openai(request, "/v1/responses:stream")
    return StreamingResponse(resp.aiter_bytes(), media_type="text/event-stream")


# --- Aliases for SDK backwards-compatibility ---

@responses_router.post("/responses")
async def create_response_alias(request: Request):
    return await create_response(request)

@responses_router.post("/responses:stream")
async def stream_response_alias(request: Request):
    return await stream_response(request)
