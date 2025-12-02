# app/utils/authy.py

from __future__ import annotations

from fastapi import HTTPException, status

from app.core.config import settings


def check_relay_key(auth_header: str | None) -> None:
    """
    Validates the incoming Authorization header against RELAY_KEY.

    Expected format:
      Authorization: Bearer <RELAY_KEY>
    """
    if not settings.RELAY_AUTH_ENABLED:
        return

    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = auth_header.split(" ", 1)[1].strip()
    if token != settings.RELAY_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid relay key",
            headers={"WWW-Authenticate": "Bearer"},
        )
