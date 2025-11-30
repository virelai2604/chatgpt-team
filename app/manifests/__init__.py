# ==========================================================
# app/manifests/__init__.py — Ground Truth Manifest Loader
# ==========================================================
"""
Dynamically loads the Ground Truth 2025.11 tool manifest (JSON)
and exposes it as TOOLS_MANIFEST for use throughout the relay.
"""

import json
import os

_manifest_path = os.path.join(os.path.dirname(__file__), "tools_manifest.json")

try:
    with open(_manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        # the manifest schema wraps the list in "tools"
        TOOLS_MANIFEST = data.get("tools", [])
except Exception as e:
    raise RuntimeError(f"Failed to load tools manifest: {_manifest_path} — {e}")
