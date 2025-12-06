# app/utils/authy.py

from __future__ import annotations

from fastapi import Request
from starlette.status import HTTP_401_UNAUTHORIZED

from app.core.config import Settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class RelayAuthError(Exception):
    """Raised when relay authentication fails."""


def _extract_bearer_token(request: Request) -> str | None:
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return None
    scheme, _, token = auth_header.partition(" ")
    if scheme.lower() != "bearer":
        return None
    return token.strip() or None


async def check_relay_key(request: Request, settings: Settings) -> None:
    """
    Enforce relay key if RELAY_AUTH_ENABLED is True.

    Authorization: Bearer <RELAY_KEY>

    If RELAY_AUTH_ENABLED is False or RELAY_KEY is empty, this is a no-op
    (i.e., public relay).
    """
    if not settings.relay_auth_enabled:
        return

    expected = settings.relay_key
    if not expected:
        # Misconfiguration: auth is enabled but no key is set.
        logger.error("Relay auth is enabled but RELAY_KEY is not configured")
        raise RelayAuthError("Relay authentication misconfigured")

    token = _extract_bearer_token(request)
    if not token or token != expected:
        logger.warning(
            "Relay auth failure from %s path=%s",
            request.client.host if request.client else "unknown",
            request.url.path,
        )
        raise RelayAuthError("Invalid relay key")
