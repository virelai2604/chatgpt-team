# ================================================================
# responses.py — Core Responses API
# ================================================================
# Implements OpenAI-compatible /v1/responses endpoints.
# Supports synchronous, streaming, and background modes.
# Integrates callable tools via /app/tools/ modules.
# ================================================================

from fastapi import APIRouter, Request, BackgroundTasks
from fastapi.responses import JSONResponse, StreamingResponse
import json, asyncio, time, uuid

# Import callable tools
from app.tools import (
    file_search,
    file_upload,
    image_generation,
    vector_store_retrieval,
    web_search,
    computer_use,
    code_interpreter,
    video_generation,
)

router = APIRouter(prefix="/v1/responses", tags=["responses"])

# ================================================================
# Tool registry
# ================================================================
tool_map = {
    "file_search": file_search,
    "file_upload": file_upload,
    "image_generation": image_generation,
    "video_generation": video_generation,
    "vector_store_retrieval": vector_store_retrieval,
    "web_search": web_search,
    "computer_use": computer_use,
    "code_interpreter": code_interpreter,
}

# ================================================================
# Helper functions
# ================================================================

def execute_tool(tool: dict):
    """Executes a registered tool by type."""
    t_type = tool.get("type")
    args = tool.get("args", {})
    module = tool_map.get(t_type)
    if not module:
        return {"tool": t_type, "status": "error", "output": {"error": "Unknown tool"}}
    try:
        if hasattr(module, "run"):
            result = module.run(args)
        elif hasattr(module, "invoke"):
            result = module.invoke(args)
        else:
            result = {"message": f"Tool {t_type} has no callable interface"}
        return {"tool": t_type, "status": "success", "output": result}
    except Exception as e:
        return {"tool": t_type, "status": "error", "output": {"error": str(e)}}


def build_response(payload: dict, tool_outputs=None):
    """Standard OpenAI-like response schema."""
    return {
        "object": "response",
        "id": f"resp_{uuid.uuid4().hex[:8]}",
        "model": payload.get("model", "gpt-4o-mini"),
        "created": int(time.time()),
        "output": [{"type": "message", "content": payload.get("input", "")}],
        "tool_outputs": tool_outputs or [],
        "status": "completed",
    }

# ================================================================
# Core Endpoints
# ================================================================

@router.post("")
async def create_response(request: Request, background_tasks: BackgroundTasks):
    """
    POST /v1/responses
    Create a text or tool-based response.
    Supports background and direct response modes.
    """
    body = await request.json()
    background = body.get("background", False)
    tools = body.get("tools", [])
    model = body.get("model", "gpt-4o-mini")

    # Execute tools (if any)
    tool_outputs = []
    for tool in tools:
        result = execute_tool(tool)
        tool_outputs.append(result)

    response = build_response(body, tool_outputs)

    if background:
        async def background_task():
            await asyncio.sleep(0.1)
        background_tasks.add_task(background_task)
        response["status"] = "queued"
        return JSONResponse(response)

    return JSONResponse(response)


@router.post(":stream")
async def stream_response(request: Request):
    """
    POST /v1/responses:stream
    Simulates a streaming response (Server-Sent Events).
    """

    async def event_stream():
        body = await request.json()
        input_text = body.get("input", "")
        chunks = [input_text[i:i+10] for i in range(0, len(input_text), 10)]
        for chunk in chunks:
            yield f"data: {json.dumps({'delta': chunk})}\n\n"
            await asyncio.sleep(0.1)
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")

# ================================================================
# Aliases for SDK compatibility
# ================================================================

# /responses
responses_router = APIRouter(prefix="/responses", tags=["responses"])

@responses_router.post("")
async def create_response_alias(request: Request):
    """Alias for /v1/responses"""
    body = await request.json()
    tools = body.get("tools", [])
    tool_outputs = [execute_tool(t) for t in tools]
    response = build_response(body, tool_outputs)
    return JSONResponse(response)


@responses_router.post(":stream")
async def stream_response_alias(request: Request):
    """Alias for /v1/responses:stream"""
    async def event_stream():
        body = await request.json()
        input_text = body.get("input", "")
        chunks = [input_text[i:i+10] for i in range(0, len(input_text), 10)]
        for chunk in chunks:
            yield f"data: {json.dumps({'delta': chunk})}\n\n"
            await asyncio.sleep(0.1)
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")

# ================================================================
# Register Aliases
# ================================================================

def register(app):
    """Manually include both versions of the responses endpoints."""
    app.include_router(router)
    app.include_router(responses_router)
    return app
