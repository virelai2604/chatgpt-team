# ============================================================
# app/api/tools_api.py — Unified Dynamic Tools API (Oct 2025)
# ============================================================

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
import importlib
import json
import os
import asyncio
import traceback

# ============================================================
# Configuration
# ============================================================

TOOLS_MANIFEST_PATH = os.getenv("TOOLS_MANIFEST", "app/manifests/tools_manifest.json")

if os.path.exists(TOOLS_MANIFEST_PATH):
    with open(TOOLS_MANIFEST_PATH, "r") as f:
        _manifest = json.load(f)
        TOOL_REGISTRY = _manifest.get("registry", [])
else:
    TOOL_REGISTRY = []

router = APIRouter(prefix="/v1/tools", tags=["Tools"])


# ============================================================
# GET /v1/tools
# ============================================================

@router.get("")
async def list_tools():
    """
    Lists all available tools dynamically.
    Schema matches OpenAI's responses tool listing spec.
    """
    tools = []

    for name in TOOL_REGISTRY:
        try:
            module = importlib.import_module(f"app.tools.{name}")
            schema = getattr(module, "TOOL_SCHEMA", {"name": name, "description": f"Tool {name}"})
            tools.append({
                "id": name,
                "name": name,
                "type": "function",
                "description": schema.get("description", f"Tool: {name}"),
                "function": {
                    "name": schema.get("name", name),
                    "description": schema.get("description", ""),
                    "parameters": schema.get("parameters", {}),
                },
            })
        except Exception as e:
            tools.append({
                "id": name,
                "name": name,
                "type": "function",
                "description": f"Error loading tool: {e}",
                "function": {
                    "name": name,
                    "description": "Load failed",
                    "parameters": {},
                },
            })

    return JSONResponse({"object": "list", "data": tools})


# ============================================================
# POST /v1/tools/{tool_name}
# ============================================================

@router.post("/{tool_name}")
async def invoke_tool(tool_name: str, request: Request):
    """
    Executes a specific tool by its name, as defined in the manifest.
    The result is formatted to match the OpenAI Responses ToolCall object:
    {
      "object": "tool_call",
      "status": "succeeded",
      "tool": "<tool_name>",
      "output": <tool result>
    }
    """
    if tool_name not in TOOL_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found in manifest")

    # Parse request body
    try:
        payload = await request.json()
    except Exception:
        payload = {}

    # Import tool module
    try:
        module = importlib.import_module(f"app.tools.{tool_name}")
    except ModuleNotFoundError:
        raise HTTPException(status_code=404, detail=f"Module 'app.tools.{tool_name}' not found")

    if not hasattr(module, "run"):
        raise HTTPException(status_code=500, detail=f"Tool '{tool_name}' missing async 'run(payload)' method")

    # Run tool safely
    try:
        result = await module.run(payload)
        return JSONResponse({
            "object": "tool_call",
            "status": "succeeded",
            "tool": tool_name,
            "output": result,
        })
    except Exception as e:
        tb = traceback.format_exc()
        raise HTTPException(status_code=500, detail=f"Tool '{tool_name}' execution failed: {e}\n{tb}")


# ============================================================
# POST /v1/tools/validate (optional)
# ============================================================

@router.post("/validate")
async def validate_registry():
    """
    Validates that all tools in the manifest can be imported and executed.
    Useful for CI/CD pipeline health checks.
    """
    errors = []
    for name in TOOL_REGISTRY:
        try:
            mod = importlib.import_module(f"app.tools.{name}")
            if not hasattr(mod, "run"):
                errors.append(f"{name}: missing 'run()'")
        except Exception as e:
            errors.append(f"{name}: {e}")

    if errors:
        raise HTTPException(status_code=500, detail={"validation_errors": errors})

    return {"status": "ok", "count": len(TOOL_REGISTRY)}
