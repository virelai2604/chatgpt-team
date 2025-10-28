# ==========================================================
# app/api/tools_api.py — Relay Tool Registry & Compatibility Layer
# ==========================================================
# Defines and manages the relay’s available tool registry.
# This module provides a central manifest used by:
#  - /v1/relay/status   → system health + tool manifest
#  - /v1/responses/tools → list of available tool names
#  - /v1/responses/tools/{tool_name} → invoke individual tools
# Also provides backward-compatible shims for older modules
# expecting `load_manifest()` and `run_tool()`.
# ==========================================================

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/v1/responses/tools", tags=["Responses"])

# =========================================================
# 🧰 TOOL REGISTRY — canonical list of available relay tools
# =========================================================
TOOL_REGISTRY = {
    "code_interpreter": {
        "description": "Execute Python code safely in a sandboxed runtime.",
        "type": "function",
    },
    "file_search": {
        "description": "Search uploaded files or vector stores using embeddings.",
        "type": "function",
    },
    "file_upload": {
        "description": "Upload files from within tool calls.",
        "type": "function",
    },
    "file_download": {
        "description": "Retrieve stored file contents.",
        "type": "function",
    },
    "vector_store_retrieval": {
        "description": "Retrieve contextual embeddings or documents from vector stores.",
        "type": "function",
    },
    "image_generation": {
        "description": "Generate or edit AI images using multimodal models.",
        "type": "function",
    },
    "video_generation": {
        "description": "Create or remix videos using Sora-family models.",
        "type": "function",
    },
    "web_search_preview": {
        "description": "Perform web searches to fetch recent or external data.",
        "type": "function",
    },
    "computer_use_preview": {
        "description": "Simulate system-level or GUI automation actions.",
        "type": "function",
    },
}

# =========================================================
# 🔍 TOOL ENDPOINTS (aligned with openapi.yaml)
# =========================================================

@router.get("", summary="List available relay tools")
async def list_tools():
    """
    Returns a list of available tools registered in the relay.
    Mirrors OpenAI's /v1/responses/tools behavior.
    """
    return JSONResponse(content={"tools": list(TOOL_REGISTRY.keys())})


@router.post("/{tool_name}", summary="Call a relay tool")
async def call_tool(tool_name: str, body: dict = None):
    """
    Dummy tool invocation endpoint.
    Accepts a tool name and returns a placeholder result.
    In production, each tool would dispatch to its own executor.
    """
    if tool_name not in TOOL_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")

    tool_info = TOOL_REGISTRY[tool_name]
    return JSONResponse(
        content={
            "tool": tool_name,
            "type": tool_info["type"],
            "description": tool_info["description"],
            "result": {
                "status": "ok",
                "echo_input": body or {},
                "note": "This is a simulated response for testing purposes."
            }
        }
    )

# =========================================================
# 🧩 COMPATIBILITY SHIMS (for legacy imports)
# =========================================================

def load_manifest():
    """
    Legacy function for modules expecting `load_manifest()`.
    Returns the tool registry manifest.
    """
    return {"tools": list(TOOL_REGISTRY.keys())}


def run_tool(tool_name: str, input_data: dict = None):
    """
    Legacy function for modules expecting `run_tool()`.
    Provides a mock dispatcher for backward compatibility.
    """
    if tool_name not in TOOL_REGISTRY:
        raise ValueError(f"Unknown tool: {tool_name}")
    tool = TOOL_REGISTRY[tool_name]
    return {
        "tool": tool_name,
        "type": tool["type"],
        "description": tool["description"],
        "result": {
            "status": "ok",
            "echo_input": input_data or {},
            "note": "Simulated execution via legacy `run_tool`."
        }
    }
