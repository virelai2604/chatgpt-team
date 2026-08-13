"""
Compatibility shim.

Some older modules referenced `app.core.settings`. The project centralizes settings in
`app.core.config`. This module re-exports the same symbols to avoid import breakage.
Still live: `app/api/forward_openai.py`, `app/core/http_client.py` and
`app/routes/files.py` import `get_settings` from here.

The docstring must stay above `from __future__ import annotations`. It used to sit
below it, which made it a bare string expression rather than a docstring — the module's
`__doc__` was None, and every import below counted as an import after a statement.
"""

from __future__ import annotations

from .config import Settings, get_settings, settings

__all__ = ["Settings", "get_settings", "settings"]
