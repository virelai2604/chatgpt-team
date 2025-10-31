# ==========================================================
# app/routes/tools.py — Ground Truth 2025.11 Unified Tool Executor
# ==========================================================
"""
Implements dynamic tool execution for /v1/responses/tools/*.

This router dynamically loads tool entrypoints from the manifest.
Supports both modern ('entrypoint') and legacy ('module' + 'function') formats.
Compatible with OpenAI Ground Truth SDK (2025.11) and GPT-5 Codex relay tests.
"""

import importlib
import inspect
import logging
from typing import Any, Dict
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from app.manifests import TOOLS_MANIFEST

logger = logging.getLogger("tools")
router = APIRouter(prefix="/v1/tools", tags=["Tools"])


# ----------------------------------------------------------
# Manifest utilities
# ----------------------------------------------------------
def load_tools_manifest() -> list[Dict[str, Any]]:
    """Return loaded manifest list."""
    return TOOLS_MANIFEST


def _resolve_entrypoint(tool_name: str, entry: Dict[str, Any]) -> tuple[str, str]:
    """Resolve entrypoint path into (module, function)."""
    if "entrypoint" in entry:
        path = entry["entrypoint"]
        if "." not in path:
            raise HTTPException(
                status_code=500,
                detail=f"Invalid entrypoint format for {tool_name}: '{path}'"
            )
        parts = path.split(".")
        return ".".join(parts[:-1]), parts[-1]
    elif "module" in entry and "function" in entry:
        return entry["module"], entry["function"]
    else:
        raise HTTPException(status_code=500, detail=f"Invalid manifest entry for {tool_name}.")


# ----------------------------------------------------------
# Core executor
# ----------------------------------------------------------
async def execute_tool_from_manifest(tool_name: str, params: Dict[str, Any]) -> Any:
    """
    Loads and executes a tool dynamically.
    Supports both sync and async callables.
    Raises HTTPException with OpenAI-style error payloads if something fails.
    """
    tools = load_tools_manifest()
    match = next((t for t in tools if t.get("name") == tool_name and t.get("enabled", True)), None)

    if not match:
        raise HTTPException(status_code=404, detail={"error": {"message": f"Tool '{tool_name}' not found", "type": "not_found"}})

    try:
        module_path, function_name = _resolve_entrypoint(tool_name, match)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": {"message": f"Invalid manifest for {tool_name}: {e}", "type": "manifest_error"}})

    try:
        mod = importlib.import_module(module_path)
        func = getattr(mod, function_name, None)
        if not callable(func):
            raise HTTPException(status_code=500, detail={"error": {"message": f"Function '{function_name}' not callable in {module_path}", "type": "invalid_function"}})

        if inspect.iscoroutinefunction(func):
            result = await func(**params)
        else:
            result = func(**params)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": {"message": f"Execution error in tool '{tool_name}': {e}", "type": "execution_error"}})


# ----------------------------------------------------------
# API Endpoints (debug + manual)
# ----------------------------------------------------------
@router.get("")
async def list_tools():
    """List all registered tools (for debugging)."""
    try:
        tools = load_tools_manifest()
        return JSONResponse({"object": "tool.list", "data": tools})
    except Exception as e:
        logger.exception("❌ Failed to list tools")
        raise HTTPException(status_code=500, detail={"error": {"message": str(e), "type": "manifest_load_error"}})


@router.post("/{tool_name}")
async def invoke_tool(tool_name: str, request: Request):
    """Manually invoke a tool (debug)."""
    try:
        payload = await request.json()
        params = payload if isinstance(payload, dict) else {}
        result = await execute_tool_from_manifest(tool_name, params)
        return JSONResponse(result)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.exception(f"❌ Tool '{tool_name}' failed: {e}")
        raise HTTPException(status_code=500, detail={"error": {"message": str(e), "type": "unexpected_error"}})
