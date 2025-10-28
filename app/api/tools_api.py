# ===============================================================
# app/api/tools_api.py — ChatGPT Team Relay (v2025 Final Edition)
# ===============================================================
# Handles tool registration, dynamic importing, and execution.
# Compatible with OpenAI Responses API + ChatGPT Actions.
# Supports both {"tools": [...]} and [...] manifest formats.
# ===============================================================

import importlib
import json
import logging
import os
from fastapi import APIRouter, Request, HTTPException

router = APIRouter(tags=["Tools"])
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------
# Manifest path (default location)
# ---------------------------------------------------------------
TOOLS_MANIFEST_PATH = os.getenv("TOOLS_MANIFEST", "app/manifests/tools_manifest.json")


# ---------------------------------------------------------------
# Load manifest (resilient to both formats)
# ---------------------------------------------------------------
def load_manifest():
    """
    Load the tools manifest JSON file.
    Supports both:
        {
          "tools": [ { "id": "...", "description": "...", "entry": "..." }, ... ]
        }
    and a flat list:
        [ { "id": "...", "description": "...", "entry": "..." }, ... ]
    """
    if not os.path.exists(TOOLS_MANIFEST_PATH):
        logger.warning(f"[ToolsAPI] Manifest not found at {TOOLS_MANIFEST_PATH}")
        return []

    try:
        with open(TOOLS_MANIFEST_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Handle {"tools": [...]} or plain list
        if isinstance(data, dict) and "tools" in data:
            tools = data["tools"]
        elif isinstance(data, list):
            tools = data
        else:
            logger.warning("[ToolsAPI] Unexpected manifest structure — returning empty list.")
            return []

        # Validate basic structure
        valid_tools = []
        for tool in tools:
            if isinstance(tool, dict) and "id" in tool:
                valid_tools.append(tool)
            else:
                logger.warning(f"[ToolsAPI] Skipping invalid tool entry: {tool}")

        return valid_tools

    except json.JSONDecodeError as e:
        logger.error(f"[ToolsAPI] Failed to parse manifest JSON: {e}")
        return []
    except Exception as e:
        logger.error(f"[ToolsAPI] Unexpected error loading manifest: {e}")
        return []


# ---------------------------------------------------------------
# Dynamic import and tool execution
# ---------------------------------------------------------------
async def run_tool(tool_name: str, payload: dict):
    """
    Dynamically import and execute a tool's `run(payload)` coroutine.
    Each tool must define:
        async def run(payload: dict) -> dict
    """
    try:
        module = importlib.import_module(f"app.tools.{tool_name}")
    except ModuleNotFoundError:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
    except Exception as e:
        logger.exception(f"[ToolsAPI] Error importing '{tool_name}': {e}")
        raise HTTPException(status_code=500, detail=str(e))

    if not hasattr(module, "run"):
        raise HTTPException(status_code=500, detail=f"Tool '{tool_name}' missing run() function")

    run_func = getattr(module, "run")
    if not callable(run_func):
        raise HTTPException(status_code=500, detail=f"Tool '{tool_name}' run() is not callable")

    try:
        logger.info(f"[ToolsAPI] Executing tool: {tool_name}")
        result = await run_func(payload)
        return result
    except Exception as e:
        logger.exception(f"[ToolsAPI] Error during '{tool_name}' execution: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------
# API endpoint: list available tools
# ---------------------------------------------------------------
@router.get("/v1/responses/tools")
async def list_tools():
    """Return all registered tools (OpenAI-compatible schema)."""
    tools = load_manifest()
    return {"object": "list", "data": tools, "count": len(tools)}


# ---------------------------------------------------------------
# API endpoint: run a tool manually
# ---------------------------------------------------------------
@router.post("/v1/responses/tools/{tool_name}")
async def call_tool(tool_name: str, request: Request):
    """Invoke a tool directly without model mediation."""
    payload = await request.json()
    result = await run_tool(tool_name, payload)
    return result


# ---------------------------------------------------------------
# Legacy alias (optional) — backward compatibility
# ---------------------------------------------------------------
def list_local_tools():
    """Legacy alias for backward compatibility (used in old responses.py)."""
    return load_manifest()
