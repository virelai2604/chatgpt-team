# ============================================================
# app/api/tools_api.py — OpenAI-Compatible Relay (v2025-Ready)
# Unified local tool discovery and execution for /v1/tools/*
# ============================================================

import os
import json
import logging
import asyncio
import pkgutil
import importlib
from pathlib import Path
from fastapi import APIRouter, HTTPException
from typing import Any, Dict, List

logger = logging.getLogger("Relay.ToolsAPI")
router = APIRouter(prefix="/v1/tools", tags=["Tools"])

# --------------------------------------------------------------------------
# 📁 Directory Configuration
# --------------------------------------------------------------------------
APP_ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = os.getenv("TOOLS_DIR", str(APP_ROOT / "tools"))
MANIFEST_PATH = os.getenv("TOOLS_MANIFEST", str(APP_ROOT / "manifests" / "tools_manifest.json"))

# --------------------------------------------------------------------------
# 🧩 Load Manifest and Tools
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
    """Dynamically import all Python modules from app/tools."""
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
# 🧠 Merge Registry + Manifest Metadata
# --------------------------------------------------------------------------
def merge_tool_metadata() -> List[Dict[str, Any]]:
    merged = []
    for tool_id, module in TOOL_REGISTRY.items():
        manifest_data = next((t for t in TOOL_MANIFEST if t.get("id") == tool_id), {})
        merged.append({
            "id": tool_id,
            "version": getattr(module, "TOOL_VERSION", manifest_data.get("version", "v1")),
            "type": getattr(module, "TOOL_TYPE", manifest_data.get("type", "function")),
            "description": manifest_data.get("description", getattr(module, "TOOL_DESCRIPTION", "No description")),
            "entry": manifest_data.get("entry", f"app/tools/{tool_id}.py"),
        })
    return merged

# --------------------------------------------------------------------------
# 📜 API Endpoints
# --------------------------------------------------------------------------
@router.get("")
def list_tools() -> Dict[str, Any]:
    """List all available tool IDs."""
    return {
        "object": "list",
        "tools": list(TOOL_REGISTRY.keys()),
        "count": len(TOOL_REGISTRY)
    }

@router.get("/schema")
def list_tool_schemas() -> Dict[str, Any]:
    """Expose JSON schemas for local tools (for GPT-5 introspection)."""
    schemas = []
    for tool_id, mod in TOOL_REGISTRY.items():
        try:
            schema = getattr(mod, "TOOL_SCHEMA", None)
            if schema:
                schema["id"] = tool_id
                schema["version"] = getattr(mod, "TOOL_VERSION", "v1")
                schemas.append(schema)
        except Exception as e:
            logger.warning(f"[ToolsAPI] Schema load error for {tool_id}: {e}")
    return {"object": "list", "schemas": schemas, "count": len(schemas)}

@router.get("/{tool_id}")
def get_tool_info(tool_id: str) -> Dict[str, Any]:
    """Retrieve detailed metadata for a specific tool."""
    merged = merge_tool_metadata()
    tool = next((t for t in merged if t["id"] == tool_id), None)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_id}' not found")
    return tool

@router.post("/{tool_id}/execute")
def execute_tool(tool_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a tool locally and return its result."""
    tool = TOOL_REGISTRY.get(tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_id}' not found")

    if not hasattr(tool, "run"):
        raise HTTPException(status_code=400, detail=f"Tool '{tool_id}' missing run()")

    try:
        result = tool.run(payload)
        return {"object": "tool.result", "tool": tool_id, "result": result}
    except Exception as e:
        logger.error(f"[ToolsAPI] Execution error in '{tool_id}': {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --------------------------------------------------------------------------
# 🔁 Async wrappers for /v1/responses orchestration
# --------------------------------------------------------------------------
def list_local_tools() -> list:
    """Expose minimal list of tool descriptors for /v1/responses injection."""
    return [
        {
            "type": getattr(mod, "TOOL_TYPE", "function"),
            "id": tool_id,
            "description": getattr(mod, "TOOL_DESCRIPTION", "")
        }
        for tool_id, mod in TOOL_REGISTRY.items()
    ]

async def run_tool(tool_name: str, payload: dict) -> dict:
    """Async-compatible tool executor for /v1/responses."""
    tool = TOOL_REGISTRY.get(tool_name)
    if not tool or not hasattr(tool, "run"):
        raise ValueError(f"Tool '{tool_name}' not found or missing run()")
    result = tool.run(payload)
    if asyncio.iscoroutine(result):
        result = await result
    return result
