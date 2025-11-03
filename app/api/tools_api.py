"""
tools_api.py — OpenAI-Compatible /v1/tools Endpoint
────────────────────────────────────────────────────────────
Implements dynamic tool invocation using manifest-based functions.

Aligned with:
  • openai-python SDK v2.61
  • openai-node SDK v6.7.0
  • OpenAI API Reference (2025-10)
Supports:
  • GET /v1/tools                → list all registered tools
  • GET /v1/tools/{tool_id}      → retrieve tool metadata
  • POST /v1/tools/execute       → execute a specific tool function
"""

import os
import json
import importlib
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from app.utils.logger import log

router = APIRouter(prefix="/v1/tools", tags=["tools"])

MANIFEST_PATH = os.getenv("TOOLS_MANIFEST_PATH", "app/manifests/tools_manifest.json")

# ------------------------------------------------------------
# Load manifest
# ------------------------------------------------------------
def load_manifest():
    try:
        with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        log.warning("[Tools] Manifest not found; returning empty list.")
        return {"tools": []}
    except json.JSONDecodeError as e:
        log.error(f"[Tools] Manifest parse error: {e}")
        return {"tools": []}


# ------------------------------------------------------------
# Helper to execute tool
# ------------------------------------------------------------
def execute_tool(tool_name: str, params: dict):
    """
    Dynamically import and execute a registered tool function.
    Tool definitions live in `app/tools/{tool_name}.py`
    Each must define `run(params: dict) -> dict`
    """
    try:
        module_path = f"app.tools.{tool_name}"
        tool_module = importlib.import_module(module_path)
        if not hasattr(tool_module, "run"):
            raise AttributeError("Tool module missing 'run' function.")
        result = tool_module.run(params)
        return {"status": "ok", "tool": tool_name, "result": result}
    except Exception as e:
        log.error(f"[Tools] Error executing tool '{tool_name}': {e}")
        return {"status": "error", "message": str(e)}


# ------------------------------------------------------------
# GET /v1/tools → List tools
# ------------------------------------------------------------
@router.get("")
async def list_tools():
    """List all available tools from manifest."""
    manifest = load_manifest()
    return JSONResponse(manifest, status_code=200)


# ------------------------------------------------------------
# GET /v1/tools/{tool_id} → Retrieve tool info
# ------------------------------------------------------------
@router.get("/{tool_id}")
async def get_tool_metadata(tool_id: str):
    """Retrieve metadata for a specific tool."""
    manifest = load_manifest()
    for tool in manifest.get("tools", []):
        if tool.get("name") == tool_id:
            return JSONResponse(tool, status_code=200)
    return JSONResponse({"error": f"Tool '{tool_id}' not found."}, status_code=404)


# ------------------------------------------------------------
# POST /v1/tools/execute → Execute tool
# ------------------------------------------------------------
@router.post("/execute")
async def execute_tool_route(request: Request):
    """Execute a specific tool defined in the manifest."""
    try:
        payload = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON body"}, status_code=400)

    tool_name = payload.get("tool")
    params = payload.get("parameters", {})

    if not tool_name:
        return JSONResponse({"error": "Missing 'tool' field"}, status_code=400)

    log.info(f"[Tools] Executing tool '{tool_name}' with parameters: {params}")
    result = execute_tool(tool_name, params)
    return JSONResponse(result, status_code=200 if result["status"] == "ok" else 500)
