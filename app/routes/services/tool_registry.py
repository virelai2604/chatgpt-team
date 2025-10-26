# app/routes/services/tool_registry.py — BIFL v2.3.4-fp
from fastapi import APIRouter

router = APIRouter(prefix="/v1/tools/registry", tags=["Tool Registry"])

@router.get("")
async def list_tools():
    """Return in-memory registered tools (none by default)."""
    return {"object": "tool_list", "count": 0, "tools": []}
