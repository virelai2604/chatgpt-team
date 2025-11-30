# app/api/tools_api.py

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger("tools_api")

router = APIRouter(prefix="", tags=["tools"])


# ---------------------------------------------------------------------------
# Tools manifest loader
# ---------------------------------------------------------------------------

_tools_cache: List[Dict[str, Any]] | None = None


def _load_tools_manifest() -> List[Dict[str, Any]]:
    """
    Load and cache the tools manifest from disk.

    settings.TOOLS_MANIFEST should be a relative or absolute path
    like "app/manifests/tools_manifest.json".

    Accepts either:
      - {"object":"list","data":[...]} (OpenAI-style list)
      - {"tools":[...]}              (custom wrapper)
      - [ ... ]                      (bare list of tools)
    """
    global _tools_cache
    if _tools_cache is not None:
        return _tools_cache

    manifest_path = Path(settings.TOOLS_MANIFEST)
    if not manifest_path.is_file():
        logger.warning("Tools manifest not found at %s", manifest_path)
        _tools_cache = []
        return _tools_cache

    try:
        content = manifest_path.read_text(encoding="utf-8")
        data: Any = json.loads(content)
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Failed to read tools manifest: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to load tools manifest")

    # Accept { "object":"list", "data":[...]} or {"tools":[...]} or a bare list
    if isinstance(data, dict):
        if "tools" in data:
            tools = data["tools"]
        elif data.get("object") == "list" and "data" in data:
            tools = data["data"]
        else:
            tools = data
    else:
        tools = data

    if not isinstance(tools, list):
        logger.error("Invalid tools manifest format; expected list.")
        raise HTTPException(status_code=500, detail="Invalid tools manifest format")

    _tools_cache = tools
    return _tools_cache


# ---------------------------------------------------------------------------
# Public endpoints
# ---------------------------------------------------------------------------


@router.get("/v1/tools")
async def list_tools() -> Dict[str, Any]:
    """
    OpenAI-style tools registry for ChatGPT Actions / Platform.

    Response shape is intentionally simple:
      {
        "object": "list",
        "data": [ {tool}, {tool}, ... ]
      }
    """
    tools = _load_tools_manifest()
    return {"object": "list", "data": tools}


@router.get("/relay/actions")
async def list_actions() -> Dict[str, Any]:
    """
    Convenience endpoint mirroring `/v1/tools`, suitable for internal
    diagnostics or custom clients that think in terms of “actions”.
    """
    tools = _load_tools_manifest()
    return {"object": "list", "data": tools}


@router.get("/relay/models")
async def list_relay_models() -> Dict[str, Any]:
    """
    Lightweight "virtual model" registry.

    This is NOT the upstream OpenAI `/v1/models`; it's a relay-specific
    description of which models the relay is configured to use, based on
    app.core.config.Settings.
    """
    default_model = settings.DEFAULT_MODEL
    realtime_model = getattr(settings, "REALTIME_MODEL", None)

    models: List[Dict[str, Any]] = [
        {
            "id": default_model,
            "object": "model",
            "owned_by": "relay",
            "relay_default": True,
        }
    ]

    if realtime_model:
        models.append(
            {
                "id": realtime_model,
                "object": "model",
                "owned_by": "relay",
                "realtime": True,
            }
        )

    return {"object": "list", "data": models}
