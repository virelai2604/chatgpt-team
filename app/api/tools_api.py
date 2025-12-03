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

    settings.TOOLS_MANIFEST may be a relative or absolute path, for example:
      - "tools_manifest.json"
      - "app/manifests/tools_manifest.json"

    Supported shapes:
      - {"object": "list", "data": [ ... ]}  (OpenAI-style list)
      - {"tools": [ ... ]}                  (custom wrapper)
      - [ { ... }, { ... } ]                (bare list of tools)
    """
    global _tools_cache
    if _tools_cache is not None:
        return _tools_cache

    path = Path(settings.TOOLS_MANIFEST)
    if not path.is_absolute():
        path = Path.cwd() / path

    if not path.exists():
        logger.error("Tools manifest not found at %s", path)
        raise HTTPException(status_code=500, detail="Tools manifest missing on relay")

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Failed to load tools manifest from %s", path)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load tools manifest: {exc}",
        ) from exc

    data: List[Dict[str, Any]]
    if isinstance(raw, list):
        data = list(raw)
    elif isinstance(raw, dict):
        if raw.get("object") == "list" and isinstance(raw.get("data"), list):
            data = list(raw["data"])
        elif isinstance(raw.get("tools"), list):
            data = list(raw["tools"])
        else:
            raise HTTPException(
                status_code=500,
                detail="Unsupported tools manifest format",
            )
    else:
        raise HTTPException(
            status_code=500,
            detail="Unsupported tools manifest format",
        )

    _tools_cache = data
    logger.info("Loaded %d tools from %s", len(data), path)
    return data


# ---------------------------------------------------------------------------
# Public endpoints
# ---------------------------------------------------------------------------


@router.get("/v1/tools")
async def list_tools() -> Dict[str, Any]:
    """
    List tools available to /v1/responses (OpenAI-compatible shape).
    """
    tools = _load_tools_manifest()
    return {
        "object": "list",
        "data": tools,
    }


@router.get("/relay/tools")
async def relay_tools() -> Dict[str, Any]:
    """
    Alias of /v1/tools for internal diagnostics and ChatGPT Actions.
    """
    return await list_tools()
