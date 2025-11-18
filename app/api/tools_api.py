"""
tools_api.py — Local Tools Registry API
───────────────────────────────────────
This module exposes a minimal OpenAI-like tools registry used by
ChatGPT Actions and internal tests.

Endpoints:
  • GET /v1/tools
  • GET /v1/tools/{tool_id}
"""

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger("relay.tools")

router = APIRouter(tags=["tools"])


def get_manifest_path(request: Request) -> Path:
    """
    Resolve the path to the tools manifest file based on app.state.TOOLS_MANIFEST.
    """
    manifest_str = getattr(request.app.state, "TOOLS_MANIFEST", "app/manifests/tools_manifest.json")
    return Path(manifest_str)


@lru_cache(maxsize=1)
def _load_manifest(path_str: str) -> Dict[str, Any]:
    """
    Load and cache the tools manifest from disk.

    The manifest is expected to be a JSON object with:
      { "object": "list", "data": [ { ...tool... }, ... ] }
    """
    path = Path(path_str)
    if not path.is_file():
        logger.error("Tools manifest not found at %s", path)
        return {"object": "list", "data": []}

    try:
        with path.open("r", encoding="utf-8") as f:
            manifest = json.load(f)
        # Basic sanity check
        if manifest.get("object") != "list":
            logger.warning("Tools manifest at %s missing object='list'", path)
        return manifest
    except Exception as exc:  # pragma: no cover (defensive)
        logger.exception("Failed to load tools manifest at %s: %s", path, exc)
        return {"object": "list", "data": []}


def get_tools_manifest(request: Request) -> Dict[str, Any]:
    """
    Dependency to retrieve the tools manifest (cached).
    """
    path = get_manifest_path(request)
    return _load_manifest(str(path))


@router.get("/v1/tools")
async def list_tools(manifest: Dict[str, Any] = Depends(get_tools_manifest)) -> Dict[str, Any]:
    """
    List all tools known to this relay.

    Shape is intentionally similar to OpenAI-style list endpoints:
      { "object": "list", "data": [ { "id": ..., "type": "function", ... }, ... ] }
    """
    return manifest


@router.get("/v1/tools/{tool_id}")
async def get_tool(
    tool_id: str,
    manifest: Dict[str, Any] = Depends(get_tools_manifest),
) -> JSONResponse:
    """
    Retrieve a single tool by id.

    Returns:
      200: { ...tool... }
      404: { "error": { "message": "...", "type": "not_found", "code": "tool_not_found" } }
    """
    tools: List[Dict[str, Any]] = manifest.get("data", [])
    for tool in tools:
        if tool.get("id") == tool_id or tool.get("name") == tool_id:
            return JSONResponse(status_code=200, content=tool)

    logger.info("Tool not found: %s", tool_id)
    return JSONResponse(
        status_code=404,
        content={
            "error": {
                "message": f"Tool '{tool_id}' not found.",
                "type": "not_found",
                "code": "tool_not_found",
            }
        },
    )
