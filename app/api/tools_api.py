# app/api/tools_api.py

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger("tools_api")

router = APIRouter(prefix="/v1", tags=["tools"])

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

    tools: List[Dict[str, Any]]
    if isinstance(data, dict):
        if data.get("object") == "list" and isinstance(data.get("data"), list):
            tools = data["data"]
        elif "tools" in data and isinstance(data["tools"], list):
            tools = data["tools"]
        else:
            raise HTTPException(
                status_code=500,
                detail="Invalid tools manifest format (dict)",
            )
    elif isinstance(data, list):
        tools = data
    else:
        raise HTTPException(
            status_code=500,
            detail="Invalid tools manifest format (must be list or dict)",
        )

    _tools_cache = tools
    logger.info("Loaded %d tools from manifest %s", len(tools), manifest_path)
    return _tools_cache


@router.get("/tools")
async def list_tools() -> Dict[str, Any]:
    """
    GET /v1/tools – return the tools manifest as an OpenAI-style list object.
    """
    tools = _load_tools_manifest()
    return {"object": "list", "data": tools}
