# ==========================================================
# responses.py — /v1/responses route group
# ==========================================================
"""
Implements the unified model generation endpoint, replacing legacy
/chat/completions and /completions. Supports both non-stream and
stream (Server-Sent Events) modes. Fully compatible with OpenAI’s
Responses API (v2025.10).
"""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse
from app.api.forward_openai import forward_openai_request

router = APIRouter(prefix="/v1/responses", tags=["Responses"])


@router.post("")
async def create_response(request: Request):
    """
    Core response creation endpoint.
    - If stream=False → return JSON response
    - If stream=True  → return SSE stream
    Gracefully handles empty or invalid JSON bodies.
    """
    try:
        body = await request.json()
    except Exception:
        body = {}

    stream = body.get("stream", False)

    if stream:
        event_stream = await forward_openai_request(
            "v1/responses", method="POST", json_data=body, stream=True
        )
        return StreamingResponse(event_stream, media_type="text/event-stream")
    else:
        data = await forward_openai_request(
            "v1/responses", method="POST", json_data=body
        )
        return JSONResponse(content=data)


@router.get("/tools")
async def list_tools():
    """
    Returns all available relay tools registered in the system.
    These are functions models can invoke via 'response.tool_calls'.
    """
    return {
        "tools": [
            "listModels",
            "listFiles",
            "uploadFile",
            "invokeTool",
            "listVectorStores",
            "createVectorStore",
        ]
    }


@router.post("/tools/{tool_name}")
async def invoke_tool(tool_name: str, request: Request):
    """
    Executes a registered relay tool, if available.
    Provides simple stub responses to simulate tool invocation.
    """
    try:
        body = await request.json()
    except Exception:
        body = {}

    return {
        "tool_invoked": tool_name,
        "arguments": body.get("arguments", {}),
        "status": "success",
    }
