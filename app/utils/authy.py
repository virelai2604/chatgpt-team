# app/utils/authy.py

from __future__ import annotations

import hmac
import logging
from typing import Optional

from fastapi import HTTPException

from app.core.config import settings

logger = logging.getLogger("relay.auth")


def _get_expected_key() -> str:
    """
    Return the configured relay key or a safe local-dev default.
    """
    key = settings.RELAY_KEY
    if not key:
        # Local dev default – matches relay_e2e_raw.py and docs
        return "dummy-local-relay-key"
    return key


def check_relay_key(auth_header: Optional[str]) -> None:
    """
    Validate Authorization header of form 'Bearer <token>' against settings.RELAY_KEY.

    If RELAY_AUTH_ENABLED is False, this is a no-op.
    On failure, raises HTTPException(401, ...).
    """
    if not settings.RELAY_AUTH_ENABLED:
        return

    if not auth_header:
        raise HTTPException(
            status_code=401,
            detail={
                "error": {
                    "message": "Missing Authorization header for relay",
                    "type": "relay_auth_error",
                    "code": "missing_relay_key",
                }
            },
        )

    try:
        scheme, token = auth_header.split(" ", 1)
    except ValueError:
        raise HTTPException(
            status_code=401,
            detail={
                "error": {
                    "message": "Malformed Authorization header",
                    "type": "relay_auth_error",
                    "code": "malformed_authorization",
                }
            },
        )

    if scheme.lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail={
                "error": {
                    "message": "Relay requires 'Bearer' Authorization scheme",
                    "type": "relay_auth_error",
                    "code": "invalid_scheme",
                }
            },
        )

    expected = _get_expected_key().encode("utf-8")
    provided = token.strip().encode("utf-8")

    if not expected:
        logger.warning("RELAY_KEY not configured; accepting any key in dev-mode")
        return

    if not hmac.compare_digest(expected, provided):
        raise HTTPException(
            status_code=401,
            detail={
                "error": {
                    "message": "Invalid relay key",
                    "type": "relay_auth_error",
                    "code": "invalid_relay_key",
                }
            },
        )
