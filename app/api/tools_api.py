# app/api/tools_api.py

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.utils.logger import get_logger  # type: ignore

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
      - {"object": "list", "data": [...]} (OpenAI-style list)
      - {"tools": [...]}                  (custom wrapper)
      - [ ... ]                           (bare list of tools)
    """
    global _tools_cache

    if _tools_cache is not None:
        return _tools_cache

    manifest_path = Path(settings.TOOLS_MANIFEST)
    if not manifest_path.exists():
        logger.warning("Tools manifest not found at %s", manifest_path)
        _tools_cache = []
        return _tools_cache

    try:
        with manifest_path.open("r", encoding="utf-8") as f:
            raw = json.load(f)
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Failed to load tools manifest: %s", exc)
        raise HTTPException(status_code=500, detail="Invalid tools manifest")

    if isinstance(raw, dict):
        if raw.get("object") == "list" and isinstance(raw.get("data"), list):
            tools = raw["data"]
        elif "tools" in raw and isinstance(raw["tools"], list):
            tools = raw["tools"]
        else:
            raise HTTPException(status_code=500, detail="Unsupported tools manifest shape")
    elif isinstance(raw, list):
        tools = raw
    else:
        raise HTTPException(status_code=500, detail="Unsupported tools manifest shape")

    _tools_cache = tools
    logger.info("Loaded %d tools from manifest", len(tools))
    return tools


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


@router.get("/v1/tools")
async def list_tools() -> Dict[str, Any]:
    """
    Return the list of declared tools (for /v1/responses.tools, etc.).

    Shape matches the OpenAI "list" object:
      {
        "object": "list",
        "data": [ ... tools ... ]
      }
    """
    tools = _load_tools_manifest()
    return {
        "object": "list",
        "data": tools,
    }
