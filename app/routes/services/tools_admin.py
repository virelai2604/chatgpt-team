# app/routes/services/tools_admin.py
"""
BIFL v2.1 – Tools Admin Router
Lets you view or refresh the current dynamic registry.
"""

import os
import json
import importlib
from fastapi import APIRouter
from app.routes.services.tool_registry import REGISTRY, TOOLS_CONFIG

router = APIRouter(prefix="/v1/tools", tags=["tools"])

@router.get("/registry")
async def list_registered_tools():
    """List all tools currently registered in REGISTRY."""
    return {"count": len(REGISTRY), "tools": list(REGISTRY.keys())}

@router.post("/refresh")
async def refresh_tools():
    """
    Reload tools dynamically from config/tools.json.
    """
    if not os.path.exists(TOOLS_CONFIG):
        return {"status": "error", "message": f"{TOOLS_CONFIG} not found"}

    try:
        with open(TOOLS_CONFIG, "r", encoding="utf-8") as f:
            tool_defs = json.load(f)

        REGISTRY.clear()
        for name, path in tool_defs.items():
            module_name, fn_name = path.rsplit(".", 1)
            mod = importlib.import_module(module_name)
            REGISTRY[name] = getattr(mod, fn_name)

        return {
            "status": "ok",
            "reloaded_tools": list(REGISTRY.keys()),
            "count": len(REGISTRY)
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
