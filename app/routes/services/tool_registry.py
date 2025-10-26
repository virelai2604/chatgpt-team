# app/api/tool_registry.py — BIFL v2.3.4-fp
import os
from fastapi import APIRouter

router = APIRouter(prefix="/v1/tools", tags=["tools"])

TOOLS_DIR = os.getenv("TOOLS_DIR", "app/tools")

def list_local_tools() -> list:
    """Return all available local tool Python modules."""
    abs_dir = os.path.abspath(TOOLS_DIR)
    if not os.path.exists(abs_dir):
        return []
    return sorted(
        [f[:-3] for f in os.listdir(abs_dir) if f.endswith(".py") and not f.startswith("__")]
    )

@router.get("")
async def get_tools():
    """List all registered local tools."""
    return {"tools": list_local_tools()}
