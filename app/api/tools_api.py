from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, List

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.utils.logger import relay_log as logger

router = APIRouter(
    prefix="/v1",
    tags=["tools"],
)

DEFAULT_TOOLS_MANIFEST_PATH = Path("app/manifests/tools_manifest.json")


def _load_tools_manifest() -> List[dict[str, Any]]:
    """
    Load the tools manifest from one of:

      1) TOOLS_MANIFEST env var:
         - If it parses as JSON → use that.
         - Else treat it as a file path.
      2) TOOLS_MANIFEST_PATH env var → file path.
      3) Default `app/manifests/tools_manifest.json`.

    The JSON file can be in one of several shapes:

      - { "object": "list", "data": [ ...tools... ] }
      - { "tools": [ ...tools... ] }
      - [ ...tools... ]

    Returns a simple Python list of tool dicts.
    """
    env_manifest = os.getenv("TOOLS_MANIFEST")
    manifest_path_env = os.getenv("TOOLS_MANIFEST_PATH")

    raw: Any

    if env_manifest:
        # Try to parse inline JSON first
        try:
            raw = json.loads(env_manifest)
            logger.info("Loaded tools manifest from TOOLS_MANIFEST (inline JSON).")
        except json.JSONDecodeError:
            # If not JSON, treat as path
            path = Path(env_manifest)
            if not path.is_file():
                raise RuntimeError(
                    f"TOOLS_MANIFEST env is neither valid JSON nor a file: {env_manifest!r}"
                )
            raw = json.loads(path.read_text(encoding="utf-8"))
            logger.info("Loaded tools manifest from TOOLS_MANIFEST file=%s", path)
    elif manifest_path_env:
        path = Path(manifest_path_env)
        if not path.is_file():
            raise RuntimeError(f"TOOLS_MANIFEST_PATH file not found: {path}")
        raw = json.loads(path.read_text(encoding="utf-8"))
        logger.info("Loaded tools manifest from TOOLS_MANIFEST_PATH=%s", path)
    else:
        path = DEFAULT_TOOLS_MANIFEST_PATH
        if not path.is_file():
            raise RuntimeError(f"Default tools_manifest.json not found at {path}")
        raw = json.loads(path.read_text(encoding="utf-8"))
        logger.info("Loaded tools manifest from default: %s", path)

    # Normalize to list
    if isinstance(raw, dict):
        if raw.get("object") == "list" and isinstance(raw.get("data"), list):
            tools = raw["data"]
        elif isinstance(raw.get("tools"), list):
            tools = raw["tools"]
        else:
            raise RuntimeError(
                "Unsupported tools manifest dict format; expected "
                "`{object:'list',data:[...]}` or `{tools:[...]}`."
            )
    elif isinstance(raw, list):
        tools = raw
    else:
        raise RuntimeError("Unsupported tools manifest format; expected list or dict.")

    if not isinstance(tools, list):
        raise RuntimeError("Tools manifest normalization did not produce a list.")

    return tools


@router.get("/tools")
async def list_tools() -> JSONResponse:
    """
    GET /v1/tools

    Return:
      {
        "object": "list",
        "data": [ ... tools from tools_manifest.json ... ]
      }
    """
    try:
        tools = _load_tools_manifest()
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to load tools manifest: %s", exc)
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "message": "Failed to load tools manifest",
                    "type": "server_error",
                }
            },
        ) from exc

    return JSONResponse(
        status_code=200,
        content={"object": "list", "data": tools},
    )


@router.get("/tools/{tool_id}")
async def get_tool(tool_id: str) -> JSONResponse:
    """
    GET /v1/tools/{tool_id}

    Return a single tool definition by its `id`. Responds with 404 if
    the tool does not exist in the manifest.
    """
    try:
        tools = _load_tools_manifest()
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to load tools manifest: %s", exc)
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "message": "Failed to load tools manifest",
                    "type": "server_error",
                }
            },
        ) from exc

    for tool in tools:
        if tool.get("id") == tool_id:
            return JSONResponse(status_code=200, content=tool)

    raise HTTPException(
        status_code=404,
        detail={
            "error": {
                "message": f"Tool '{tool_id}' not found",
                "type": "invalid_request_error",
                "param": "tool_id",
            }
        },
    )
