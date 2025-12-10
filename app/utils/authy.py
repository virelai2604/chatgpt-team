# app/utils/authy.py

from __future__ import annotations

import hmac
import logging
from typing import Optional

from fastapi import HTTPException, status

from app.core.config import settings

logger = logging.getLogger("relay.auth")


def _get_expected_key() -> str:
    """
    Return the configured relay key or a safe local-dev default.

    If RELAY_KEY is not set we fall back to "dummy-local-relay-key",
    which matches relay_e2e_raw.py and the docs.
    """
    key = settings.RELAY_KEY
    if not key:
        return "dummy-local-relay-key"
    return key


def _extract_bearer_token(auth_header: Optional[str]) -> Optional[str]:
    """
    Parse Authorization header of form 'Bearer <token>'.

    Returns token string, or None if header is missing.
    Raises HTTPException with string `detail` on malformed cases.
    """
    if auth_header is None:
        return None

    try:
        scheme, token = auth_header.split(" ", 1)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed Authorization header",
        )

    if scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Relay requires 'Bearer' Authorization scheme",
        )

    token = token.strip()
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
      1. X-Relay-Key header (used by relay_e2e_raw.py)
      2. Authorization: Bearer <token> (used by OpenAI SDK client)

    If RELAY_AUTH_ENABLED is False, this is a no-op.

    On failure, raises HTTPException(status_code=..., detail="<string>").
    """
    # If auth is disabled, skip entirely
    if not settings.RELAY_AUTH_ENABLED:
        return

    # Prefer explicit X-Relay-Key
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
        # Configuration bug; log and fail closed
        logger.error("Relay auth misconfigured: RELAY_KEY is empty when auth is enabled")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Relay auth misconfigured",
        )

    if not hmac.compare_digest(expected, provided):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid relay key",
        )
