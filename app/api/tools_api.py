from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/v1/tools", tags=["tools"])


def _load_tools_manifest() -> List[Dict[str, Any]]:
    """
    Load tools manifest either from:
    - TOOLS_MANIFEST (JSON string OR file path), or
    - TOOLS_MANIFEST_PATH (JSON file path), or
    - default: app/manifests/tools_manifest.json

    The manifest JSON is expected to be either:
      - { "object": "list", "data": [ ... ] }
      - { "tools": [ ... ] }
      - [ ... ]  # plain list
    """
    manifest_env = os.getenv("TOOLS_MANIFEST")
    manifest_path_env = os.getenv("TOOLS_MANIFEST_PATH")

    manifest_path: str | None = None

    # 1) If TOOLS_MANIFEST is set, decide whether it's inline JSON or a path.
    if manifest_env:
        stripped = manifest_env.lstrip()
        # Looks like JSON → parse as JSON
        if stripped.startswith("{") or stripped.startswith("["):
            try:
                data = json.loads(manifest_env)
            except json.JSONDecodeError as exc:
                raise RuntimeError("Invalid TOOLS_MANIFEST JSON") from exc

            if isinstance(data, dict):
                tools = data.get("data") or data.get("tools")
            else:
                tools = data

            if not isinstance(tools, list):
                raise RuntimeError(
                    "TOOLS_MANIFEST JSON must be a list or an object with 'data' or 'tools' list"
                )
            return tools
        else:
            # Treat value as path
            manifest_path = manifest_env

    # 2) Fall back to TOOLS_MANIFEST_PATH
    if manifest_path is None:
        if manifest_path_env:
            manifest_path = manifest_path_env
        else:
            manifest_path = "app/manifests/tools_manifest.json"

    # 3) Resolve path relative to project root if needed
    path_obj = Path(manifest_path)
    if not path_obj.is_absolute():
        # project root = app/.. (adjust if needed)
        path_obj = Path(__file__).resolve().parents[2] / path_obj

    if not path_obj.is_file():
        raise RuntimeError(f"Tools manifest not found at {path_obj}")

    # 4) Load JSON from file
    with path_obj.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict):
        tools = data.get("data") or data.get("tools")
    else:
        tools = data

    if not isinstance(tools, list):
        raise RuntimeError(
            "Tools manifest JSON must be a list or an object with 'data' or 'tools' list"
        )

    return tools


@router.get("", summary="List available tools")
async def list_tools() -> Dict[str, Any]:
    """
    GET /v1/tools

    Returns:
      {
        "object": "list",
        "data": [ ...tool defs... ]
      }
    """
    tools = _load_tools_manifest()
    return {"object": "list", "data": tools}


@router.get("/{tool_id}", summary="Get a single tool definition")
async def get_tool(tool_id: str) -> Dict[str, Any]:
    """
    GET /v1/tools/{tool_id}
    """
    tools = _load_tools_manifest()
    for tool in tools:
        if str(tool.get("id")) == tool_id:
            return tool
    raise HTTPException(status_code=404, detail="Tool not found")
