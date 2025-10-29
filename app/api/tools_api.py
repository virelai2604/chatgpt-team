# ==========================================================
# app/api/tools_api.py — Relay Tool Registry and Invocation Layer
# ==========================================================
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from typing import List, Dict, Any

# Registry of available tools
TOOLS_REGISTRY: List[Dict[str, Any]] = [
    {"id": "code_interpreter", "name": "code_interpreter", "description": "Executes Python code and returns stdout or errors.", "type": "function"},
    {"id": "file_search", "name": "file_search", "description": "Searches uploaded or vector-stored files for relevant content.", "type": "function"},
    {"id": "file_upload", "name": "file_upload", "description": "Uploads a file into the relay’s store.", "type": "function"},
    {"id": "file_download", "name": "file_download", "description": "Downloads a file by ID.", "type": "function"},
    {"id": "vector_store_retrieval", "name": "vector_store_retrieval", "description": "Retrieves semantically relevant chunks from vector stores.", "type": "function"},
    {"id": "image_generation", "name": "image_generation", "description": "Generates images using DALL·E or compatible models.", "type": "function"},
    {"id": "web_search", "name": "web_search", "description": "Performs live web searches for fresh information.", "type": "function"},
    {"id": "video_generation", "name": "video_generation", "description": "Creates short video clips or animations.", "type": "function"},
    {"id": "computer_use", "name": "computer_use", "description": "Simulates desktop control for automation (placeholder).", "type": "function"}
]

async def list_tools() -> List[Dict[str, Any]]:
    """Return a list of available tools."""
    return TOOLS_REGISTRY

async def call_tool(tool_name: str, body: Dict[str, Any]) -> JSONResponse:
    """Mock tool invocation — echoes the input for now."""
    tool = next((t for t in TOOLS_REGISTRY if t["name"] == tool_name), None)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")

    result = {
        "tool": tool_name,
        "input": body,
        "status": "executed",
        "output": f"Mock result from tool '{tool_name}'"
    }
    return JSONResponse(result)
