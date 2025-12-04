from __future__ import annotations

from app.core.config import settings


def is_auth_enabled() -> bool:
    """
    Tiny helper used by tests to confirm whether relay auth is active.
    """
    return settings.RELAY_AUTH_ENABLED
