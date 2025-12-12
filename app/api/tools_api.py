from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


def _inject_required_endpoints(manifest: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensure manifest advertises the endpoints your tests (and tooling) expect.
    We keep this additive to avoid breaking existing consumers.
    """
    endpoints = manifest.setdefault("endpoints", [])
    if isinstance(endpoints, list):
        wanted = [
            {"method": "POST", "path": "/v1/responses"},
            {"method": "POST", "path": "/v1/responses/compact"},
        ]
        have = {(e.get("method"), e.get("path")) for e in endpoints if isinstance(e, dict)}
        for w in wanted:
            key = (w["method"], w["path"])
            if key not in have:
                endpoints.append(w)
    return manifest


def load_tools_manifest() -> Dict[str, Any]:
    """
    Load the tools manifest JSON from disk and augment it with runtime metadata.
    If the file is missing, return a minimal manifest rather than 500/404.
    """
    path = Path(str(settings.TOOLS_MANIFEST_PATH))
    now = datetime.now(timezone.utc).isoformat()

    if not path.exists():
        logger.warning("Tools manifest file not found at %s; returning minimal manifest", path)
        minimal = {
            "name": "chatgpt-team-relay",
            "generated_at": now,
            "base_url": str(settings.BASE_URL).rstrip("/"),
            "endpoints": [],
        }
        return _inject_required_endpoints(minimal)

    try:
        raw = path.read_text(encoding="utf-8")
        manifest = json.loads(raw)
    except Exception as e:
        logger.error("Failed to parse tools manifest: %s", e)
        raise HTTPException(status_code=500, detail="Failed to load tools manifest")

    manifest["generated_at"] = now
    manifest["base_url"] = str(settings.BASE_URL).rstrip("/")
    return _inject_required_endpoints(manifest)


@router.get("/v1/tools/manifest")
async def get_tools_manifest() -> Dict[str, Any]:
    logger.info("Serving tools manifest")
    return load_tools_manifest()


# Alias expected by your integration test.
@router.get("/manifest")
async def get_tools_manifest_root() -> Dict[str, Any]:
    logger.info("Serving tools manifest (root alias)")
    return load_tools_manifest()
