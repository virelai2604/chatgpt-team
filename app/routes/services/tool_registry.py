# app/routes/services/tool_registry.py
# BIFL v2.2 – Tool Registry API
# Loads and manages relay tools from config/tools.json

import os
import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/v1/tools/registry", tags=["Tool Registry"])

TOOLS_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "..", "config", "tools.json")

# Load tools from file
def load_tools():
    try:
        with open(TOOLS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict) and "tools" in data:
                return data["tools"]
            return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load tools.json: {str(e)}")


@router.get("/")
async def list_tools():
    """List all tools registered in config/tools.json."""
    tools = load_tools()
    return {"object": "tool_list", "count": len(tools), "tools": tools}


@router.get("/{tool_name}")
async def get_tool(tool_name: str):
    """Retrieve a specific tool by name."""
    tools = load_tools()
    for t in tools:
        if t.get("name") == tool_name:
            return {"object": "tool", "tool": t}
    raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")


@router.post("/reload")
async def reload_tools():
    """Reload tools.json from disk (hot refresh)."""
    try:
        tools = load_tools()
        return {"object": "reload", "status": "ok", "count": len(tools)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/meta")
async def registry_metadata():
    """Return registry metadata for diagnostics."""
    return {
        "object": "registry",
        "file_path": TOOLS_PATH,
        "exists": os.path.exists(TOOLS_PATH),
    }
