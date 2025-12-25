from __future__ import annotations

from fastapi import HTTPException, Request

from app.core.config import get_settings

settings = get_settings()


def _extract_relay_key(request: Request) -> str | None:
    """Extract relay key from either Authorization: Bearer <key> or X-Relay-Key."""
    auth_header = request.headers.get("authorization") or request.headers.get("Authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        return auth_header.split(" ", 1)[1].strip() or None

    x_relay_key = request.headers.get("x-relay-key") or request.headers.get("X-Relay-Key")
    if x_relay_key:
        return x_relay_key.strip() or None

    return None


def check_relay_key(request: Request) -> None:
    """
    Enforce relay auth for /v1 paths when enabled.

    Error strings are intentionally stable because tests assert exact values.
    """
    if not settings.RELAY_AUTH_ENABLED:
        return

    relay_key = _extract_relay_key(request)
    if relay_key is None:
        raise HTTPException(status_code=401, detail="Missing relay key")

    if relay_key != settings.RELAY_KEY:
        raise HTTPException(status_code=401, detail="Invalid relay key")
