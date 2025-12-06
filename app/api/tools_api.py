# app/api/tools_api.py

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, status

from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/v1", tags=["tools"])


def _load_tools_manifest() -> Dict[str, Any]:
    manifest_path = Path(settings.tools_manifest)
    if not manifest_path.is_file():
        raise FileNotFoundError(str(manifest_path))
    with manifest_path.open("r", encoding="utf-8") as f:
        return json.load(f)


@router.get("/tools", summary="List relay tools manifest")
async def list_tools() -> Dict[str, Any]:
    """
    Expose a relay-level tools manifest. This is a convenience layer for
    agentic clients that want to introspect capabilities.
    """
    try:
        manifest = _load_tools_manifest()
    except FileNotFoundError:
        logger.error("Tools manifest not found at %s", settings.tools_manifest)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Tools manifest not configured",
        )
    return manifest
