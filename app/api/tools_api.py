"""
tools_api.py — Hosted Tool Registry (OpenAI-compatible)
───────────────────────────────────────────────────────
Implements /v1/tools and /v1/tools/{tool_id} endpoints.

This is optional for openai-python 2.x and openai-node 6.x, since
the SDKs normally configure tools inline on the request. However,
it is useful for agents or diagnostics that probe /v1/tools.

IMPORTANT:
  • We do NOT try to auto-sync all official hosted tools here.
    The canonical tools config stays on the /v1/responses body.
"""

import os
import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/v1", tags=["tools"])

MANIFEST_PATH = os.path.join(
    os.path.dirname(__file__),
    "../manifests/tools_manifest.json",
)


def load_manifest() -> dict:
    """Safely load the local tools manifest (OpenAI-style schema)."""
    try:
        with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
            manifest = json.load(f)

            # Normalize older "data" shape to "tools" if needed
            if "data" in manifest and "tools" not in manifest:
                manifest["tools"] = manifest.pop("data")

            manifest.setdefault("object", "list")
            manifest.setdefault("tools", [])
            return manifest
    except (FileNotFoundError, json.JSONDecodeError):
        return {"object": "list", "tools": []}


@router.get("/tools")
async def list_tools():
    """
    Returns a list of available tools in OpenAI-compatible format:

    {
      "object": "list",
      "tools": [ { ... } ]
    }
    """
    manifest = load_manifest()

    for tool in manifest.get("tools", []):
        tool.setdefault("object", "tool")
        tool.setdefault("type", "function")
        tool.setdefault("name", tool.get("id"))

    return JSONResponse(status_code=200, content=manifest)


@router.get("/tools/{tool_id}")
async def get_tool(tool_id: str):
    """Retrieve metadata for one tool by ID or name."""
    manifest = load_manifest()
    for tool in manifest.get("tools", []):
        if tool.get("id") == tool_id or tool.get("name") == tool_id:
            return JSONResponse(status_code=200, content=tool)
    raise HTTPException(status_code=404, detail=f"Tool '{tool_id}' not found.")
