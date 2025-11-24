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
