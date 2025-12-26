"""
Compatibility shim.

Some modules historically imported settings/get_settings from app.core.settings.
The canonical implementation lives in app.core.config.
"""

from __future__ import annotations

from app.core.config import get_settings, settings

__all__ = ["get_settings", "settings"]
