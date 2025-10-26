import os
import json
import logging
import pkgutil
import importlib
from fastapi import APIRouter, HTTPException
from typing import Any, Dict, List

# -----------------------------------------------------------------------------
# Tools API - BIFL 2.3.4-fp
# -----------------------------------------------------------------------------
# Provides:
#   • /v1/tools                 → list available tools
#   • /v1/tools/{id}            → get info about a tool
#   • /v1/tools/{id}/execute    → run a tool locally
#   • /v1/tools/schema          → expose JSON schema for all tools (UI + GPT-5)
# -----------------------------------------------------------------------------

logger = logging.getLogger("BIFL.ToolsAPI")
router = APIRouter(prefix="/v1/tools", tags=["Tools"])

TOOLS_DIR = os.getenv("TOOLS_DIR", "app/tools")
MANIFEST_PATH = os.path.join(TOOLS_DIR, "tools_manifest.json")


# -----------------------------------------------------------------------------
# Load manifest file (optional)
# -----------------------------------------------------------------------------
def load_manifest() -> List[Dict[str, Any]]:
    try:
        if os.path.exists(MANIFEST_PATH):
            with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
                manifest = json.load(f)
                if isinstance(manifest, list):
                    return manifest
        return []
    except Exception as e:
        logger.warning(f"[ToolsAPI] Failed to load manifest: {e}")
        return []


# -----------------------------------------------------------------------------
# Dynamic tool loader
# -----------------------------------------------------------------------------
def load_tools() -> Dict[str, Any]:
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


# -----------------------------------------------------------------------------
# GET /v1/tools
# -----------------------------------------------------------------------------
@router.get("")
def list_tools() -> Dict[str, Any]:
    """List all loaded tool IDs."""
    return {"tools": list(TOOL_REGISTRY.keys())}


# -----------------------------------------------------------------------------
# GET /v1/tools/{tool_id}
# -----------------------------------------------------------------------------
@router.get("/{tool_id}")
def get_tool_info(tool_id: str) -> Dict[str, Any]:
    """Retrieve metadata about a specific tool."""
    tool = TOOL_REGISTRY.get(tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_id}' not found")

    manifest = next((t for t in TOOL_MANIFEST if t.get("id") == tool_id), {})

    return {
        "id": tool_id,
        "version": getattr(tool, "TOOL_VERSION", "v1"),
        "type": getattr(tool, "TOOL_TYPE", "function"),
        "description": manifest.get("description", getattr(tool, "TOOL_DESCRIPTION", "No description")),
        "entry": manifest.get("entry", f"app/tools/{tool_id}.py"),
    }


# -----------------------------------------------------------------------------
# POST /v1/tools/{tool_id}/execute
# -----------------------------------------------------------------------------
@router.post("/{tool_id}/execute")
def execute_tool(tool_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Run the tool's local function implementation."""
    tool = TOOL_REGISTRY.get(tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_id}' not found")

    try:
        if not hasattr(tool, "run"):
            raise HTTPException(status_code=400, detail=f"Tool '{tool_id}' has no run() function")
        result = tool.run(payload)
        return {"tool": tool_id, "result": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ToolsAPI] Execution error in '{tool_id}': {e}")
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------------------------------------------------------
# GET /v1/tools/schema
# -----------------------------------------------------------------------------
@router.get("/schema")
def list_tool_schemas() -> Dict[str, Any]:
    """
    Expose JSON schema for each tool for UI + GPT-5 model introspection.
    Each tool module can define TOOL_SCHEMA = {...}.
    """
    try:
        schemas: List[Dict[str, Any]] = []
        for tool_id, mod in TOOL_REGISTRY.items():
            schema = getattr(mod, "TOOL_SCHEMA", None)
            if schema:
                schemas.append(schema)
            else:
                # Fallback if no schema is defined
                schemas.append({
                    "name": tool_id,
                    "description": getattr(mod, "TOOL_DESCRIPTION", "No schema provided."),
                    "parameters": {"type": "object", "properties": {}}
                })

        return {"schemas": schemas}

    except Exception as e:
        logger.error(f"[ToolsAPI] Failed to compile tool schemas: {e}")
        raise HTTPException(status_code=500, detail=str(e))
