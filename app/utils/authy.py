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

    In this project, if RELAY_KEY is not set we fall back to
    "dummy-local-relay-key", which is also what the e2e script uses.
    """
    key = settings.RELAY_KEY
    if not key:
        # Local dev default – matches relay_e2e_raw.py and docs
        return "dummy-local-relay-key"
    return key


def _extract_bearer_token(auth_header: Optional[str]) -> str:
    """
    Parse Authorization header of form 'Bearer <token>'.

    Raises HTTPException with string `detail` on error, matching the
    expectations in test_relay_auth_middleware.
    """
    if not auth_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
        )

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


def check_relay_key(auth_header: Optional[str]) -> None:
    """
    Validate Authorization header of form 'Bearer <token>' against settings.RELAY_KEY.

    If RELAY_AUTH_ENABLED is False, this is a no-op.
    On failure, raises HTTPException(401, detail="<string>") – the tests
    assert on that exact shape.
    """
    # If auth is disabled, skip entirely
    if not settings.RELAY_AUTH_ENABLED:
        return

    token = _extract_bearer_token(auth_header)

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
