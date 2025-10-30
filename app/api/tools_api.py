# ==========================================================
# app/api/tools_api.py — Relay Tool Registry & Invocation
# ==========================================================
"""
Defines the relay’s internal tool registry and mock execution layer.
Implements the backend for /v1/responses/tools endpoints.
"""

from fastapi import HTTPException
from typing import List, Dict, Any

TOOLS_REGISTRY: List[Dict[str, Any]] = [
    {"id": "code_interpreter", "name": "code_interpreter", "description": "Executes Python code.", "type": "function"},
    {"id": "file_search", "name": "file_search", "description": "Searches uploaded or vector-stored files.", "type": "function"},
    {"id": "image_generation", "name": "image_generation", "description": "Generates images using DALL·E models.", "type": "function"},
    {"id": "web_search", "name": "web_search", "description": "Performs live web searches for fresh information.", "type": "function"},
    {"id": "video_generation", "name": "video_generation", "description": "Creates short videos or animations.", "type": "function"},
    {"id": "vector_store_retrieval", "name": "vector_store_retrieval", "description": "Retrieves semantically relevant chunks.", "type": "function"},
]


async def list_tools() -> List[Dict[str, Any]]:
    """Return the full list of available tools."""
    return TOOLS_REGISTRY


async def call_tool(tool_name: str, body: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a mock tool invocation."""
    tool = next((t for t in TOOLS_REGISTRY if t["name"] == tool_name), None)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")

    return {
        "tool": tool_name,
        "input": body,
        "status": "executed",
        "output": f"Mock result from tool '{tool_name}'"
    }
