# ==========================================================
# app/routes/tools.py — Ground Truth Tool Execution Layer (v2025.10)
# ==========================================================
"""
Updated to support the compact registry format used by:
  C:\Tools\ChatGpt Domain\Cloudflare\chatgpt-team\app\manifests\tools_manifest.json

Example:
{
  "version": "2025.10",
  "registry": [
    "code_interpreter",
    "file_search",
    "file_upload",
    "file_download",
    "vector_store_retrieval",
    "image_generation",
    "web_search",
    "video_generation",
    "computer_use"
  ]
}
"""

import os
import json
import logging
import importlib
import inspect
import asyncio
from typing import Any, Dict

logger = logging.getLogger("tools")

TOOLS_MANIFEST_PATH = os.getenv(
    "TOOLS_MANIFEST_PATH",
    "app/manifests/tools_manifest.json"
)

# Default convention mapping
DEFAULT_TOOL_MAP = {
    "code_interpreter": ("app.tools.code_interpreter", "run_code"),
    "file_search": ("app.tools.file_search", "search_files"),
    "file_upload": ("app.tools.file_upload", "upload_file"),
    "file_download": ("app.tools.file_download", "download_file"),
    "vector_store_retrieval": ("app.tools.vector_store_retrieval", "retrieve_vectors"),
    "image_generation": ("app.tools.image_generation", "generate_image"),
    "web_search": ("app.tools.web_search", "search_web"),
    "video_generation": ("app.tools.video_generation", "generate_video"),
    "computer_use": ("app.tools.computer_use", "run_computer_task"),
}

# ----------------------------------------------------------
# Load and normalize manifest
# ----------------------------------------------------------
if os.path.exists(TOOLS_MANIFEST_PATH):
    with open(TOOLS_MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)
        version = manifest.get("version", "unknown")
        registry = manifest.get("registry", [])
        _TOOL_REGISTRY = [
            {
                "name": t,
                "module": DEFAULT_TOOL_MAP.get(t, (None, None))[0],
                "function": DEFAULT_TOOL_MAP.get(t, (None, None))[1],
            }
            for t in registry
            if t in DEFAULT_TOOL_MAP
        ]
        logger.info(f"🧩 Loaded {len(_TOOL_REGISTRY)} tools from manifest v{version}")
else:
    logger.warning(f"⚠️ tools_manifest.json not found at {TOOLS_MANIFEST_PATH}")
    _TOOL_REGISTRY = []


# ----------------------------------------------------------
# Registry helpers
# ----------------------------------------------------------
def list_registered_tools() -> list[dict]:
    """Return a normalized tool registry list."""
    return _TOOL_REGISTRY


def get_tool_entry(name: str) -> dict | None:
    """Find tool definition by name."""
    for t in _TOOL_REGISTRY:
        if t["name"] == name:
            return t
    return None


# ----------------------------------------------------------
# Tool executor
# ----------------------------------------------------------
async def execute_tool_from_manifest(tool_name: str, params: Dict[str, Any]) -> Any:
    """Execute a tool dynamically using its module + function."""
    entry = get_tool_entry(tool_name)
    if not entry:
        raise ValueError(f"Tool '{tool_name}' not found in manifest registry.")

    module_name, function_name = entry["module"], entry["function"]
    if not module_name or not function_name:
        raise ValueError(f"Invalid manifest entry for '{tool_name}'.")

    logger.info(f"🛠️ Executing tool: {tool_name} ({function_name})")

    try:
        module = importlib.import_module(module_name)
        func = getattr(module, function_name)
    except Exception as e:
        raise RuntimeError(f"Failed to import {module_name}.{function_name}: {e}")

    if not callable(func):
        raise TypeError(f"Function {function_name} in {module_name} is not callable")

    try:
        if inspect.iscoroutinefunction(func):
            result = await func(**params)
        else:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, lambda: func(**params))
        logger.debug(f"✅ Tool {tool_name} completed successfully")
        return result
    except Exception as e:
        logger.error(f"❌ Tool {tool_name} failed: {e}")
        raise RuntimeError(f"Tool {tool_name} execution failed: {e}")
