from __future__ import annotations

from fastapi import HTTPException, Request

from app.core.config import settings


def check_relay_key(request: Request) -> None:
    """
    Enforce relay key authentication for /v1/* endpoints when enabled.

    Tests require exact error messages:
      - "Missing relay key" (no trailing period)
      - "Invalid relay key"
    """
    if not getattr(settings, "RELAY_AUTH_ENABLED", False):
        return

    relay_key = request.headers.get("x-relay-key") or request.headers.get("authorization")
    if not relay_key:
        raise HTTPException(status_code=401, detail="Missing relay key")

    # Allow Authorization: Bearer <key>
    if relay_key.lower().startswith("bearer "):
        relay_key = relay_key[7:].strip()

    if relay_key != getattr(settings, "RELAY_KEY", ""):
        raise HTTPException(status_code=401, detail="Invalid relay key")
