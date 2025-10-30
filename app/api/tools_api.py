# ==========================================================
# app/api/tools_api.py — Relay-Internal Tools API
# ==========================================================
"""
Internal ChatGPT Team Relay endpoint for inspecting and invoking
registered tools directly.

⚠️ This is *not* part of the OpenAI API spec.
It exists for diagnostics, introspection, and debugging only.
Public SDKs use /v1/responses/tools instead.
"""

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
import os, json

router = APIRouter(prefix="/v1/tools_api", tags=["Relay Tools API"])

TOOLS_MANIFEST_PATH = os.getenv("TOOLS_MANIFEST", "app/manifests/tools_manifest.json")

# ==========================================================
# Built-in relay tools (always available)
# ==========================================================
BUILTIN_TOOLS = [
    {
        "id": "code_interpreter",
        "name": "code_interpreter",
        "type": "function",
        "description": "Executes Python code snippets in a sandboxed environment.",
        "function": {
            "name": "code_interpreter",
            "parameters": {"type": "object", "properties": {"code": {"type": "string"}}},
        },
    },
    {
        "id": "file_search",
        "name": "file_search",
        "type": "function",
        "description": "Searches uploaded or stored files for relevant content.",
        "function": {
            "name": "file_search",
            "parameters": {"type": "object", "properties": {"query": {"type": "string"}}},
        },
    },
    {
        "id": "vector_store_retrieval",
        "name": "vector_store_retrieval",
        "type": "function",
        "description": "Retrieves semantically similar documents from vector stores.",
        "function": {
            "name": "vector_store_retrieval",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "top_k": {"type": "integer", "default": 5},
                },
            },
        },
    },
]

# ==========================================================
# Helper: Load external manifest (if present)
# ==========================================================
def load_manifest_tools():
    tools = BUILTIN_TOOLS.copy()
    if os.path.exists(TOOLS_MANIFEST_PATH):
        try:
            with open(TOOLS_MANIFEST_PATH, "r") as f:
                manifest = json.load(f)
                for t in manifest.get("registry", []):
                    if not any(x["id"] == t for x in tools):
                        tools.append(
                            {
                                "id": t,
                                "name": t,
                                "type": "function",
                                "description": f"Tool from manifest: {t}",
                                "function": {"name": t, "parameters": {}},
                            }
                        )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Invalid tools manifest: {e}")
    return tools

# ==========================================================
# GET /v1/tools_api
# ==========================================================
@router.get("")
async def list_tools():
    """
    Returns the full relay tool registry — both built-ins and
    any defined in tools_manifest.json.
    """
    tools = load_manifest_tools()
    return JSONResponse({"object": "list", "data": tools})

# ==========================================================
# GET /v1/tools_api/{tool_name}
# ==========================================================
@router.get("/{tool_name}")
async def get_tool(tool_name: str):
    """Return metadata for a specific relay tool."""
    tools = load_manifest_tools()
    tool = next((t for t in tools if t["id"] == tool_name or t["name"] == tool_name), None)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
    return JSONResponse(tool)

# ==========================================================
# POST /v1/tools_api/{tool_name}
# ==========================================================
@router.post("/{tool_name}")
async def invoke_tool(tool_name: str, request: Request):
    """
    Simulate tool execution locally (for debugging).
    Returns a standardized "tool_call" object like the
    OpenAI Responses API would.
    """
    try:
        payload = await request.json()
    except Exception:
        payload = {}

    tools = load_manifest_tools()
    tool = next((t for t in tools if t["id"] == tool_name or t["name"] == tool_name), None)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")

    # Simulate execution
    output = f"Executed tool '{tool_name}' with input: {json.dumps(payload)}"

    return JSONResponse(
        {
            "object": "tool_call",
            "id": f"local_tool_{tool_name}",
            "tool_name": tool_name,
            "status": "succeeded",
            "output": output,
        }
    )
