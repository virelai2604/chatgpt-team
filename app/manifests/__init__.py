# ==========================================================
# app/manifests/__init__.py — Ground Truth Manifest Loader
# ==========================================================
"""
Loads tools from app/manifests/tools_manifest.json and exposes TOOLS_MANIFEST.

Supports BOTH shapes:
  - {"tools": [ ... ]}   (original intention)
  - {"object":"list","data":[ ... ]} (your current file shape)
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List


_manifest_path = os.path.join(os.path.dirname(__file__), "tools_manifest.json")


def _coerce_tools_list(raw: Any) -> List[Dict[str, Any]]:
    if isinstance(raw, list):
        return [t for t in raw if isinstance(t, dict)]

    if isinstance(raw, dict):
        tools = raw.get("tools")
        if isinstance(tools, list):
            return [t for t in tools if isinstance(t, dict)]

        data = raw.get("data")
        if isinstance(data, list):
            return [t for t in data if isinstance(t, dict)]

    return []


try:
    with open(_manifest_path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    TOOLS_MANIFEST = _coerce_tools_list(raw)
except Exception as e:
    raise RuntimeError(f"Failed to load tools manifest: {_manifest_path} — {e}")
