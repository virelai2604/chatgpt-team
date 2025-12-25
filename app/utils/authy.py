from __future__ import annotations

from fastapi import HTTPException, Request

from app.core.config import get_settings


def check_relay_key(request: Request) -> None:
    """
    Validate relay key (client -> relay) when enabled.

    Expected header name: settings.RELAY_AUTH_HEADER (default: X-Relay-Key)
    Expected value: settings.RELAY_KEY

    Raises:
        HTTPException(401) with detail "Missing relay key" or "Invalid relay key"
    """
    settings = get_settings()
    if not settings.RELAY_AUTH_ENABLED:
        return

    header_name = settings.RELAY_AUTH_HEADER
    required = settings.RELAY_KEY

    if not required:
        raise HTTPException(status_code=500, detail="Relay auth enabled but no RELAY_KEY configured")

    provided = request.headers.get(header_name)

    # Baseline requires EXACT wording (no trailing period).
    if provided is None or provided == "":
        raise HTTPException(status_code=401, detail="Missing relay key")

    if provided != required:
        raise HTTPException(status_code=401, detail="Invalid relay key")
