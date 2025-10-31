# ==========================================================
# app/api/tools_api.py — Ground Truth Tool API Bridge (v2025.11)
# ==========================================================
"""
Provides the API bridge between /v1/responses and the tool execution system.

This module is responsible for:
  • Invoking tools defined in the Ground Truth manifest.
  • Returning unified error payloads in OpenAI-style schema.
  • Listing available tools via the manifest loader.

This version is fully aligned with GPT-5 Codex / Ground Truth SDK 2025.11.
"""

import logging
from fastapi import HTTPException
from typing import Any, Dict

# Imports from the unified tools router
from app.routes.tools import execute_tool_from_manifest, load_tools_manifest

logger = logging.getLogger("tools_api")


# ----------------------------------------------------------
# Tool Execution
# ----------------------------------------------------------
async def execute_tool(tool_name: str, params: Dict[str, Any]) -> Any:
    """
    Execute a tool by name using the Ground Truth manifest entrypoint.
    Wraps execute_tool_from_manifest() and ensures OpenAI-style errors.

    Args:
        tool_name: The tool identifier (e.g., 'image_generation').
        params: JSON parameters to be passed to the tool.
    Returns:
        Any result returned by the tool (JSON serializable).
    Raises:
        HTTPException: If the tool fails, is missing, or returns invalid output.
    """
    try:
        logger.info(f"🧠 [tools_api] Executing tool '{tool_name}' with params: {params}")
        result = await execute_tool_from_manifest(tool_name, params)
        logger.info(f"✅ [tools_api] Tool '{tool_name}' executed successfully.")
        return result
    except HTTPException:
        raise  # Already formatted correctly
    except Exception as e:
        logger.exception(f"❌ [tools_api] Tool '{tool_name}' execution failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "message": f"Execution error in '{tool_name}': {e}",
                    "type": "execution_error",
                }
            },
        )


# ----------------------------------------------------------
# Manifest Access
# ----------------------------------------------------------
def get_registered_tools() -> list[Dict[str, Any]]:
    """
    Returns the list of registered tools from the loaded manifest.

    This is a read-only helper for debugging and introspection.
    """
    try:
        logger.debug("📜 Loading registered tools from manifest")
        tools = load_tools_manifest()
        return tools
    except Exception as e:
        logger.exception("❌ Failed to load tools manifest")
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "message": f"Failed to load tools manifest: {e}",
                    "type": "manifest_error",
                }
            },
        )


# ----------------------------------------------------------
# Compatibility Helpers (optional)
# ----------------------------------------------------------
def tool_exists(name: str) -> bool:
    """
    Check whether a tool is registered in the current manifest.
    """
    try:
        tools = load_tools_manifest()
        return any(t.get("name") == name and t.get("enabled", True) for t in tools)
    except Exception:
        return False
