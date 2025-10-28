# ============================================================
# app/api/tools_api.py — Live Dynamic Tool Executor (Final Fixed)
# ============================================================
# Dynamically loads tools from tools_manifest.json or app/tools/.
# Supports GPT-5 /v1/responses tool calls with real execution.
# Handles manifest-relative and absolute paths gracefully.
# ============================================================

import os
import json
import logging
import asyncio
import importlib.util
from pathlib import Path
from fastapi import APIRouter, HTTPException
from typing import Any, Dict, List

logger = logging.getLogger("Relay.ToolsAPI")
router = APIRouter(prefix="/v1/tools", tags=["Tools"])

# -------------------------------------------------------------
# 📁 Paths
# -------------------------------------------------------------
APP_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = os.getenv("TOOLS_MANIFEST", str(APP_ROOT / "manifests" / "tools_manifest.json"))

# Lazy cache — only populated when a tool is executed
TOOL_REGISTRY: Dict[str, Any] = {}

# -------------------------------------------------------------
# 🧩 Manifest loader
# -------------------------------------------------------------
def load_manifest() -> List[Dict[str, Any]]:
    """Read tool metadata from the manifest file."""
    try:
        with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and "tools" in data:
            return data["tools"]
        elif isinstance(data, list):
            return data
    except Exception as e:
        logger.warning(f"[ToolsAPI] Failed to load manifest: {e}")
    return []

TOOL_MANIFEST = load_manifest()

# -------------------------------------------------------------
# 🧠 Helper: dynamically import a tool
# -------------------------------------------------------------
def _import_tool(tool_name: str, entry_path: Path):
    """Import a tool module dynamically from its Python file."""
    if not entry_path.exists():
        raise FileNotFoundError(f"Tool file not found: {entry_path}")

    spec = importlib.util.spec_from_file_location(tool_name, str(entry_path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    TOOL_REGISTRY[tool_name] = module
    logger.info(f"[ToolsAPI] Loaded tool '{tool_name}' from {entry_path}")
    return module

# -------------------------------------------------------------
# 📜 API endpoints
# -------------------------------------------------------------
@router.get("")
def list_tools() -> Dict[str, Any]:
    """Return all available tools from manifest."""
    ids = [t["id"] for t in TOOL_MANIFEST]
    return {"object": "list", "tools": ids, "count": len(ids)}

@router.get("/{tool_id}")
def get_tool_info(tool_id: str) -> Dict[str, Any]:
    """Return metadata for a specific tool."""
    tool = next((t for t in TOOL_MANIFEST if t.get("id") == tool_id), None)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_id}' not found")
    return tool

# -------------------------------------------------------------
# 🧰 OpenAI-compatible schema builder
# -------------------------------------------------------------
def list_local_tools() -> list:
    """Expose tools for /v1/responses injection."""
    tools = []
    for t in TOOL_MANIFEST:
        tools.append({
            "type": "function",
            "function": {
                "name": t["id"],
                "description": t.get("description", ""),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "input": {
                            "type": "string",
                            "description": "Input payload"
                        }
                    },
                    "required": ["input"]
                }
            }
        })
    return tools

# -------------------------------------------------------------
# ⚙️ Core: real dynamic tool executor
# -------------------------------------------------------------
async def run_tool(tool_name: str, payload: dict) -> dict:
    """
    Execute a tool dynamically from manifest.
    Loads the module if not cached, calls its run() function,
    and returns the result. Handles flexible entry paths.
    """
    # 1️⃣ Resolve manifest entry
    entry = next((t.get("entry") for t in TOOL_MANIFEST if t.get("id") == tool_name), None)
    if not entry:
        raise ValueError(f"Tool '{tool_name}' not found in manifest")

    # 2️⃣ Normalize path (handles both app/tools/... and tools/...)
    entry_path = (Path.cwd() / entry).resolve()
    if not entry_path.exists():
        # Fallback 1: relative to /app directory
        alt_path = (APP_ROOT / Path(entry).name).resolve()
        # Fallback 2: directly inside /app/tools
        alt_path2 = (APP_ROOT / "tools" / Path(entry).name).resolve()

        if alt_path.exists():
            entry_path = alt_path
        elif alt_path2.exists():
            entry_path = alt_path2
        else:
            raise FileNotFoundError(f"Tool file not found: {entry_path}")

    # 3️⃣ Import if not loaded
    module = TOOL_REGISTRY.get(tool_name)
    if not module:
        module = _import_tool(tool_name, entry_path)

    # 4️⃣ Execute tool’s run() function
    if not hasattr(module, "run"):
        raise AttributeError(f"Tool '{tool_name}' missing run() function")

    try:
        result = module.run(payload)
        if asyncio.iscoroutine(result):
            result = await result
        return result
    except Exception as e:
        logger.error(f"[ToolsAPI] Error executing {tool_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
