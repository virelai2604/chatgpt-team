"""
app/api/tools_api.py

Internal relay tool manager for the P4 Orchestrator.
Compatible with OpenAI SDK 2.6.1 schema.

Tools are never exposed as /v1/tools routes in production.
They are invoked internally from /v1/responses based on the
'tool_calls' array in the model's output.
"""

import os
import json
import importlib
import inspect
import asyncio
import logging
from typing import Any, Dict

from fastapi import APIRouter
from fastapi.responses import JSONResponse

logger = logging.getLogger("tools_api")
logger.setLevel(logging.INFO)

router = APIRouter(tags=["internal-tools"])

TOOLS_MANIFEST = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "manifests", "tools_manifest.json"
)


# ─────────────────────────────────────────────
# Tool Registry Loader
# ─────────────────────────────────────────────
class ToolRegistry:
    def __init__(self):
        self.tools: Dict[str, dict] = {}
        self._load_manifest()

    def _load_manifest(self):
        try:
            if not os.path.exists(TOOLS_MANIFEST):
                logger.warning(f"⚠️ No tools manifest found at {TOOLS_MANIFEST}")
                return
            with open(TOOLS_MANIFEST, "r", encoding="utf-8") as f:
                data = json.load(f)
            for tool in data.get("tools", []):
                if tool.get("enabled", True):
                    name = tool["tool_name"]
                    self.tools[name] = tool
            logger.info(f"🔧 Loaded {len(self.tools)} tools from manifest.")
        except Exception as e:
            logger.exception(f"Failed to load tools manifest: {e}")

    def get_tool(self, name: str) -> dict | None:
        return self.tools.get(name)


# Instantiate global registry
registry = ToolRegistry()


# ─────────────────────────────────────────────
# Internal Tool Execution
# ─────────────────────────────────────────────
async def execute_tool(tool_name: str, args: dict) -> Any:
    """
    Executes a tool defined in tools_manifest.json
    Supports async, sync, and generator functions.
    """
    tool = registry.get_tool(tool_name)
    if not tool:
        raise ValueError(f"Tool '{tool_name}' not found or disabled.")

    entrypoint = tool.get("entrypoint")
    if not entrypoint:
        raise ValueError(f"Tool '{tool_name}' has no entrypoint defined.")

    module_path, func_name = entrypoint.rsplit(".", 1)
    try:
        module = importlib.import_module(module_path)
        func = getattr(module, func_name)
    except ModuleNotFoundError:
        raise ImportError(f"Module not found for tool '{tool_name}': {module_path}")
    except AttributeError:
        raise ImportError(f"Function '{func_name}' not found in {module_path}")

    try:
        # Async generator
        if inspect.isasyncgenfunction(func):
            results = []
            async for item in func(**args):
                results.append(item)
            return results

        # Async function
        if inspect.iscoroutinefunction(func):
            return await func(**args)

        # Sync generator
        if inspect.isgeneratorfunction(func):
            return list(func(**args))

        # Sync function
        return func(**args)

    except Exception as e:
        logger.exception(f"Tool execution failed ({tool_name}): {e}")
        raise RuntimeError(str(e)) from e


# ─────────────────────────────────────────────
# Optional Debug Endpoint
# ─────────────────────────────────────────────
@router.get("/debug/tools")
async def list_tools():
    """Returns manifest-loaded tools for debugging."""
    return JSONResponse({"object": "list", "data": list(registry.tools.keys())})
