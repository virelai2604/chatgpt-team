# ==========================================================
# app/routes/tools.py — Relay Tools Endpoint
# ==========================================================
"""
Implements /v1/responses/tools for function calling and registry listing.
Backed by app/api/tools_api.py (mock tools for Ground Truth Edition).
"""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from app.api.tools_api import list_tools, call_tool

router = APIRouter(tags=["Tools"])


@router.get("/v1/responses/tools", status_code=200)
async def get_tools():
    """List all registered relay tools."""
    tools = await list_tools()
    return JSONResponse(content={"object": "list", "data": tools}, status_code=200)


@router.post("/v1/responses/tools/{tool_name}", status_code=200)
async def invoke_tool(tool_name: str, request: Request):
    """Invoke a tool by name."""
    body = await request.json()
    result = await call_tool(tool_name, body)
    return JSONResponse(content=result, status_code=200)
