# ============================================================
# app/api/tools_api.py — BIFL 2.3.4-fp (Merged + Linked)
# Fully connected to app/tools/* and app/manifests/tools_manifest.json
# ============================================================

import os
import json
import logging
import pkgutil
import importlib
from pathlib import Path
from fastapi import APIRouter, HTTPException
from typing import Any, Dict, List

logger = logging.getLogger("BIFL.ToolsAPI")
router = APIRouter(prefix="/v1/tools", tags=["Tools"])

# --------------------------------------------------------------------------
# 📁 Directory Configuration
# --------------------------------------------------------------------------
APP_ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = os.getenv("TOOLS_DIR", str(APP_ROOT / "tools"))
MANIFEST_PATH = os.getenv("TOOLS_MANIFEST", str(APP_ROOT / "manifests" / "tools_manifest.json"))

# --------------------------------------------------------------------------
# 📜 Load Manifest and Tools
# --------------------------------------------------------------------------
def load_manifest() -> List[Dict[str, Any]]:
    """Load optional manifest file for tool metadata."""
    try:
        if os.path.exists(MANIFEST_PATH):
            with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict) and "tools" in data:
                    return data["tools"]
                elif isinstance(data, list):
                    return data
    except Exception as e:
        logger.warning(f"[ToolsAPI] Manifest load failed: {e}")
    return []

def load_tools() -> Dict[str, Any]:
    """Dynamically import all Python modules from app/tools/."""
    tools = {}
    for _, name, _ in pkgutil.iter_modules([TOOLS_DIR]):
        try:
            module = importlib.import_module(f"app.tools.{name}")
            tool_id = getattr(module, "TOOL_ID", name)
            tools[tool_id] = module
            logger.info(f"[ToolsAPI] Registered tool: {tool_id}")
        except Exception as e:
            logger.error(f"[ToolsAPI] Failed to load {name}: {e}")
    return tools

TOOL_REGISTRY: Dict[str, Any] = load_tools()
TOOL_MANIFEST: List[Dict[str, Any]] = load_manifest()

# --------------------------------------------------------------------------
# 🧩 GET /v1/tools
# --------------------------------------------------------------------------
@router.get("")
def list_tools() -> Dict[str, Any]:
    """Return a list of all available tool IDs."""
    return {
        "tools": list(TOOL_REGISTRY.keys()),
        "count": len(TOOL_REGISTRY),
        "source": "dynamic"
    }

# --------------------------------------------------------------------------
# 🧩 GET /v1/tools/schema
# --------------------------------------------------------------------------
@router.get("/schema")
def list_tool_schemas() -> Dict[str, Any]:
    """Expose JSON schemas for each local tool (UI + GPT-5 introspection)."""
    schemas = []
    for tool_id, mod in TOOL_REGISTRY.items():
        try:
            schema = getattr(mod, "TOOL_SCHEMA", None)
            if schema:
                schemas.append(schema)
            else:
                schemas.append({
                    "name": tool_id,
                    "description": getattr(mod, "TOOL_DESCRIPTION", "No schema provided."),
                    "parameters": {"type": "object", "properties": {}}
                })
        except Exception as e:
            logger.warning(f"[ToolsAPI] Schema error for {tool_id}: {e}")
    return {"schemas": schemas, "count": len(schemas)}

# --------------------------------------------------------------------------
# 🧩 GET /v1/tools/{tool_id}
# --------------------------------------------------------------------------
@router.get("/{tool_id}")
def get_tool_info(tool_id: str) -> Dict[str, Any]:
    """Get metadata about a specific tool."""
    tool = TOOL_REGISTRY.get(tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_id}' not found")

    manifest = next((t for t in TOOL_MANIFEST if t.get("id") == tool_id), {})
    return {
        "id": tool_id,
        "version": getattr(tool, "TOOL_VERSION", manifest.get("version", "v1")),
        "type": getattr(tool, "TOOL_TYPE", manifest.get("type", "function")),
        "description": manifest.get("description", getattr(tool, "TOOL_DESCRIPTION", "No description")),
        "entry": manifest.get("entry", f"app/tools/{tool_id}.py"),
    }

# --------------------------------------------------------------------------
# 🧩 POST /v1/tools/{tool_id}/execute
# --------------------------------------------------------------------------
@router.post("/{tool_id}/execute")
def execute_tool(tool_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a tool locally (sandboxed)."""
    tool = TOOL_REGISTRY.get(tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_id}' not found")

    try:
        if not hasattr(tool, "run"):
            raise HTTPException(status_code=400, detail=f"Tool '{tool_id}' missing run()")
        result = tool.run(payload)
        return {"tool": tool_id, "result": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ToolsAPI] Execution error in '{tool_id}': {e}")
        raise HTTPException(status_code=500, detail=str(e))
