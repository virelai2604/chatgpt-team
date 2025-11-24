from __future__ import annotations

import os

from fastapi import Header, HTTPException, status

RELAY_KEY = os.getenv("RELAY_KEY")
RELAY_AUTH_ENABLED = os.getenv("RELAY_AUTH_ENABLED", "false").lower() in {
    "1",
    "true",
    "yes",
}


def check_relay_key(authorization_header: str | None) -> None:
    """
    Core RELAY_KEY validation logic.

    Used by:
      - FastAPI dependency (verify_relay_key)
      - RelayAuthMiddleware (auth at middleware level)
    """
    if not RELAY_AUTH_ENABLED:
        # Auth globally disabled; nothing to do.
        return

    if not RELAY_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="RELAY_KEY is not configured",
        )

    if not authorization_header or not authorization_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
        )

    token = authorization_header.split(" ", 1)[1]
    if token != RELAY_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid relay key",
        )


async def verify_relay_key(
    authorization: str | None = Header(default=None),
) -> None:
    """
    Simple bearer-token guard for relay endpoints, usable as a dependency.

    - If RELAY_AUTH_ENABLED is false => no-op (always allow).
    - Else:
        Expect header: Authorization: Bearer <RELAY_KEY>
    """
    check_relay_key(authorization)
