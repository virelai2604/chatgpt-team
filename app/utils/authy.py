from __future__ import annotations

import hmac

from fastapi import HTTPException

from app.core.config import settings


def _get_expected_key() -> str:
    """
    Prefer settings.RELAY_KEY, but keep a fallback to RELAY_AUTH_TOKEN.
    """
    if getattr(settings, "RELAY_KEY", None):
        return str(settings.RELAY_KEY)
    token = getattr(settings, "RELAY_AUTH_TOKEN", None)
    return str(token or "")


def check_relay_key(*, authorization: str | None, x_relay_key: str | None) -> None:
    """
    Validate the inbound request key against settings.RELAY_KEY.

    Accepted locations:
      - X-Relay-Key: <token>
      - Authorization: Bearer <token>

    Behavior:
      - If RELAY_AUTH_ENABLED is false, this is a no-op.
      - If enabled and no key is configured, raise 500 (misconfiguration).
      - If missing token, raise 401 "Missing relay key".
      - If token is invalid, raise 401 "Invalid relay key".
      - If Authorization is present but not Bearer, raise 401 mentioning Bearer.
    """
    if not getattr(settings, "RELAY_AUTH_ENABLED", False):
        return

    expected = _get_expected_key().encode("utf-8")
    if not expected:
        raise HTTPException(
            status_code=500,
            detail="Relay auth misconfigured: RELAY_KEY is empty when auth is enabled",
        )

    presented: list[str] = []
    if x_relay_key:
        presented.append(x_relay_key)

    if authorization:
        parts = authorization.split(" ", 1)
        if len(parts) == 2 and parts[0].lower() == "bearer":
            presented.append(parts[1])
        else:
            raise HTTPException(
                status_code=401,
                detail="Authorization header must use Bearer scheme",
            )

    if not presented:
        raise HTTPException(status_code=401, detail="Missing relay key")

    for token in presented:
        if hmac.compare_digest(token.encode("utf-8"), expected):
            return

    raise HTTPException(status_code=401, detail="Invalid relay key")
