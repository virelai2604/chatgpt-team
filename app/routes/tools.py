from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
import json
import os
import httpx

router = APIRouter(prefix="/v1/responses/tools", tags=["Tools"])

# Path to your local manifest (optional)
TOOLS_MANIFEST_PATH = os.getenv("TOOLS_MANIFEST", "app/manifests/tools_manifest.json")

# Upstream OpenAI configuration (for proxy fallback)
OPENAI_BASE = os.getenv("OPENAI_BASE_URL", "https://api.openai.com")
API_KEY = os.getenv("OPENAI_API_KEY")
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}


# ==========================================================
# GET /v1/responses/tools
# ==========================================================
@router.get("")
async def list_tools():
    """
    GET /v1/responses/tools
    Returns a list of available tools compatible with Responses API.
    Matches OpenAI's schema exactly:
    {
      "object": "list",
      "data": [ { "id": "code_interpreter", "name": "...", "type": "function", ... } ]
    }
    """
    tools = []

    # Load local manifest if it exists
    if os.path.exists(TOOLS_MANIFEST_PATH):
        try:
            with open(TOOLS_MANIFEST_PATH, "r") as f:
                manifest = json.load(f)
                # Manifest may define "registry": [...]
                registry = manifest.get("registry", [])
                for name in registry:
                    tools.append({
                        "id": name,
                        "name": name,
                        "type": "function",
                        "description": f"Tool for {name.replace('_', ' ')}.",
                        "function": {
                            "name": name,
                            "description": f"Executes the {name} tool.",
                            "parameters": {}
                        }
                    })
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Invalid tools manifest: {e}")

    # Fallback: define core built-ins if manifest missing or empty
    if not tools:
        tools = [
            {
                "id": "code_interpreter",
                "name": "code_interpreter",
                "type": "function",
                "description": "Executes Python code snippets in a secure sandbox.",
                "function": {
                    "name": "code_interpreter",
                    "description": "Runs Python code.",
                    "parameters": {"type": "object", "properties": {"code": {"type": "string"}}}
                }
            },
            {
                "id": "file_search",
                "name": "file_search",
                "type": "function",
                "description": "Searches uploaded or vector-stored files for relevant content.",
                "function": {
                    "name": "file_search",
                    "description": "Performs text search within uploaded files.",
                    "parameters": {"type": "object", "properties": {"query": {"type": "string"}}}
                }
            }
        ]

    return JSONResponse({"object": "list", "data": tools})


# ==========================================================
# POST /v1/responses/tools/{tool_name}
# ==========================================================
@router.post("/{tool_name}")
async def invoke_tool(tool_name: str, request: Request):
    """
    POST /v1/responses/tools/{tool_name}
    Invokes a specific tool. 
    If local, simulate execution; if not, forward to OpenAI upstream.
    """
    try:
        payload = await request.json()
    except Exception:
        payload = {}

    # Simulate known tools locally
    if tool_name == "code_interpreter":
        code = payload.get("code", "print('Hello')")
        return {
            "object": "tool_call",
            "id": "local_tool_call_code_interpreter",
            "tool_name": "code_interpreter",
            "status": "succeeded",
            "output": f"Executed code: {code}"
        }

    if tool_name == "file_search":
        query = payload.get("query", "")
        return {
            "object": "tool_call",
            "id": "local_tool_call_file_search",
            "tool_name": "file_search",
            "status": "succeeded",
            "output": f"Search results for '{query}' (mock data)."
        }

    # Forward unknown tools to OpenAI upstream if available
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{OPENAI_BASE}/v1/responses/tools/{tool_name}",
            headers=HEADERS,
            json=payload,
        )
        if r.status_code == 404:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found upstream.")
        return JSONResponse(r.json(), status_code=r.status_code)
