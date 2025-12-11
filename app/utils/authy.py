# app/utils/authy.py

from __future__ import annotations

import hmac
from typing import Optional

from fastapi import HTTPException, status

from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


def _get_expected_key() -> str:
    """
    Return the configured relay key as a plain string.

    Prefer settings.RELAY_KEY, but keep a fallback to RELAY_AUTH_TOKEN
    for compatibility with older configs.
    """
    if getattr(settings, "RELAY_KEY", None):
        return settings.RELAY_KEY

    # Legacy / fallback name
    token = getattr(settings, "RELAY_AUTH_TOKEN", None)
    return token or ""


def _extract_bearer_token(auth_header: Optional[str]) -> Optional[str]:
    """
    Parse an Authorization header of the form 'Bearer <token>'.

    Returns the token string, or None if the header is missing.

    Raises HTTPException(401) if the header is present but malformed.
    """
    if not auth_header:
        return None

    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Relay requires 'Bearer' Authorization scheme",
        )

    token = parts[1].strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing relay key",
        )

    return token


def check_relay_key(
    auth_header: Optional[str],
    x_relay_key: Optional[str],
) -> None:
    """
    Validate incoming relay key.

    Priority:
      1. X-Relay-Key header (used by relay_e2e_raw.py / tools)
      2. Authorization: Bearer <token> (used by SDK-style clients)

    If RELAY_AUTH_ENABLED is False, this is a no-op.

    On failure, raises HTTPException(status_code=..., detail="<string>").
    """
    # If auth is disabled, skip entirely
    if not getattr(settings, "RELAY_AUTH_ENABLED", False):
        return

    # Prefer explicit X-Relay-Key when present
    token: Optional[str] = None
    if x_relay_key:
        token = x_relay_key.strip()
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing relay key",
            )
    else:
        # Fall back to Authorization header
        token = _extract_bearer_token(auth_header)

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing relay key",
        )

    expected = _get_expected_key().encode("utf-8")
    provided = token.encode("utf-8")

    if not expected:
        # Config bug; log and fail closed
        logger.error(
            "Relay auth misconfigured: RELAY_KEY is empty when auth is enabled",
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Relay auth misconfigured",
        )

    if not hmac.compare_digest(expected, provided):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid relay key",
        )
