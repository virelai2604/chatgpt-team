# app/middleware/relay_auth.py

from typing import Callable, Awaitable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

from ..core.config import get_settings
from ..utils.logger import get_logger

logger = get_logger(__name__)


class RelayAuthMiddleware(BaseHTTPMiddleware):
    """
    Optional shared-secret auth in front of the relay.

    If RELAY_AUTH_ENABLED is true, every request must include a valid
    Authorization header of the form:

        Authorization: Bearer <RELAY_KEY>

    This mirrors app/utils/authy.check_relay_key so that:
      * middleware protects *all* routes at the edge; and
      * authy can be used for more granular checks inside handlers.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        settings = get_settings()

        # Fast path: auth disabled
        if not getattr(settings, "RELAY_AUTH_ENABLED", False):
            return await call_next(request)

        auth_header = request.headers.get("Authorization")

        if not auth_header:
            logger.warning("Missing Authorization header on relay request")
            return JSONResponse(
                status_code=401,
                content={
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
            logger.warning("Malformed Authorization header on relay request")
            return JSONResponse(
                status_code=401,
                content={
                    "error": {
                        "message": "Malformed Authorization header",
                        "type": "relay_auth_error",
                        "code": "malformed_authorization",
                    }
                },
            )

        if scheme.lower() != "bearer":
            logger.warning("Invalid auth scheme on relay request: %s", scheme)
            return JSONResponse(
                status_code=401,
                content={
                    "error": {
                        "message": "Relay requires 'Bearer' Authorization scheme",
                        "type": "relay_auth_error",
                        "code": "invalid_scheme",
                    }
                },
            )

        expected = (settings.RELAY_KEY or "").strip()
        provided = token.strip()

        if not expected:
            # Treat missing key as misconfiguration; reject rather than silently allow.
            logger.error(
                "RELAY_AUTH_ENABLED is true, but RELAY_KEY is not configured; rejecting request"
            )
            return JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "message": "Relay auth misconfigured (no RELAY_KEY)",
                        "type": "relay_auth_error",
                        "code": "missing_relay_key_config",
                    }
                },
            )

        if expected != provided:
            logger.warning("Invalid relay key presented")
            return JSONResponse(
                status_code=401,
                content={
                    "error": {
                        "message": "Invalid relay key",
                        "type": "relay_auth_error",
                        "code": "invalid_relay_key",
                    }
                },
            )

        return await call_next(request)
