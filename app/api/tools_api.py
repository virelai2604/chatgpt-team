# ==========================================================
# app/api/tools_api.py — Tools Manifest Endpoints
# ==========================================================
"""
Serves the relay's tools manifest at:
  - GET /manifest
  - GET /v1/manifest

The integration tests expect:
  data["endpoints"]["responses"] includes "/v1/responses"
  data["endpoints"]["responses_compact"] includes "/v1/responses/compact"
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, cast

from fastapi import APIRouter

from ..core.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["manifest"])


def _read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _extract_tools(payload: Any) -> List[Dict[str, Any]]:
    """
    Accept multiple on-disk shapes safely:
      - {"tools": [...]}                       (legacy/expected by manifests/__init__.py in your note)
      - {"data": [...], "object": "list", ...} (what your /manifest currently returns)
      - [...]                                   (raw list of tool dicts)
    """
    if isinstance(payload, list):
        return cast(List[Dict[str, Any]], payload)

    if isinstance(payload, dict):
        tools = payload.get("tools")
        if isinstance(tools, list):
            return cast(List[Dict[str, Any]], tools)

        data = payload.get("data")
        if isinstance(data, list):
            return cast(List[Dict[str, Any]], data)

    return []


def load_tools_manifest() -> List[Dict[str, Any]]:
    """
    Loads tools from:
      1) settings.TOOLS_MANIFEST (if it's a list of tools)
      2) settings.TOOLS_MANIFEST (if it's a path to JSON)
      3) fallback: app/manifests/tools_manifest.json
    """
    settings = get_settings()
    manifest_setting: Union[str, List[Dict[str, Any]], None] = getattr(settings, "TOOLS_MANIFEST", None)

    # If someone injected the tools directly (already parsed)
    if isinstance(manifest_setting, list):
        return manifest_setting

    # If it's a path string
    if isinstance(manifest_setting, str) and manifest_setting.strip():
        path = Path(manifest_setting)
        if path.exists():
            try:
                return _extract_tools(_read_json(path))
            except Exception as e:
                logger.warning("Failed reading TOOLS_MANIFEST from %s: %s", path, e)

    # Fallback to app/manifests/tools_manifest.json relative to this file
    fallback_path = Path(__file__).resolve().parents[1] / "manifests" / "tools_manifest.json"
    if fallback_path.exists():
        try:
            return _extract_tools(_read_json(fallback_path))
        except Exception as e:
            logger.warning("Failed reading fallback tools manifest from %s: %s", fallback_path, e)

    return []


def build_manifest_response(tools: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    settings = get_settings()
    tools_list = tools if tools is not None else load_tools_manifest()

    # Keep your current behavior: endpoints.responses lists both paths,
    # but ALSO add endpoints.responses_compact for the test expectation.
    endpoints: Dict[str, List[str]] = {
        "responses": ["/v1/responses", "/v1/responses/compact"],
        "responses_compact": ["/v1/responses/compact"],
    }

    relay_name = (
        getattr(settings, "relay_name", None)
        or getattr(settings, "project_name", None)
        or "ChatGPT Team Relay"
    )

    return {
        "object": "list",
        "data": tools_list,
        "endpoints": endpoints,
        "meta": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "relay_name": relay_name,
        },
    }


@router.get("/manifest")
async def get_manifest_root() -> Dict[str, Any]:
    # Returning a dict is fine—FastAPI will serialize it as JSON. 
    logger.info("Serving tools manifest (root alias)")
    return build_manifest_response()


@router.get("/v1/manifest")
async def get_manifest_v1() -> Dict[str, Any]:
    logger.info("Serving tools manifest (/v1)")
    return build_manifest_response()
