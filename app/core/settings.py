from __future__ import annotations

"""
Compatibility shim.

Some older modules referenced `app.core.settings`. The project centralizes settings in
`app.core.config`. This module re-exports the same symbols to avoid import breakage.
"""

from .config import Settings, get_settings, settings

__all__ = ["Settings", "get_settings", "settings"]
