# app/routes/actions.py

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

logger = logging.getLogger("relay.actions")

router = APIRouter(prefix="/v1", tags=["actions", "tools"])

# Adjust to your actual location
TOOLS_MANIFEST_PATH = (
    Path(__file__).resolve().parent.parent / "manifests" / "tools_manifest.json"
)


def load_tools_manifest() -> dict[str, Any]:
    """
    Load the tools manifest from disk.

    This is used both by the relay API (for /v1/tools) and by the P4 orchestrator
    when wiring tools into the agent. :contentReference[oaicite:7]{index=7}
    """
    if not TOOLS_MANIFEST_PATH.exists():
        logger.error("tools_manifest.json not found at %s", TOOLS_MANIFEST_PATH)
        raise HTTPException(status_code=500, detail="Tools manifest not found")

    try:
        with TOOLS_MANIFEST_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to load tools_manifest.json")
        raise HTTPException(status_code=500, detail="Failed to load tools manifest") from exc

    if not isinstance(data, dict) or data.get("object") != "list":
        logger.error("Invalid tools_manifest.json format: %s", data)
        raise HTTPException(status_code=500, detail="Invalid tools manifest format")

    return data


@router.get("/tools")
async def list_tools() -> JSONResponse:
    """
    List all tools available to the agent, mirroring the GPTs/Actions concept.

    This is *not* an OpenAI upstream endpoint; it is a local relay endpoint
    exposing your manifest to the orchestrator / UI.
    """
    manifest = load_tools_manifest()
    return JSONResponse(content=manifest)


@router.get("/tools/{tool_id}")
async def get_tool(tool_id: str) -> JSONResponse:
    """
    Fetch a single tool definition by id from tools_manifest.json.
    """
    manifest = load_tools_manifest()
    tools = manifest.get("data", [])
    for tool in tools:
        if tool.get("id") == tool_id:
            return JSONResponse(content=tool)

    raise HTTPException(status_code=404, detail=f"Tool '{tool_id}' not found")
