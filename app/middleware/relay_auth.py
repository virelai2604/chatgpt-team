# app/middleware/relay_auth.py

from __future__ import annotations

import logging
from typing import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings

logger = logging.getLogger("relay")


class RelayAuthMiddleware(BaseHTTPMiddleware):
    """
    Simple header-based auth for the relay.

    If RELAY_AUTH_ENABLED is true, all requests must include:
      X-Relay-Key: <RELAY_KEY>
    otherwise a 401 is returned.
    """

    def __init__(self, app, relay_key: str | None = None) -> None:
        super().__init__(app)
        # Prefer explicit key if passed; fall back to settings
        self.relay_key = relay_key or settings.RELAY_KEY
        self.auth_enabled = settings.RELAY_AUTH_ENABLED

        logger.info(
            "RelayAuthMiddleware initialized",
            extra={
                "auth_enabled": self.auth_enabled,
                "relay_key_configured": bool(self.relay_key),
            },
        )

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if not self.auth_enabled:
            return await call_next(request)

        expected = self.relay_key
        provided = request.headers.get("X-Relay-Key")

        if not expected:
            logger.warning(
                "RelayAuthMiddleware enabled but RELAY_KEY is not set; "
                "request will be rejected"
            )

        if not expected or provided != expected:
            logger.warning(
                "Unauthorized request to relay",
                extra={
                    "path": request.url.path,
                    "has_header": provided is not None,
                },
            )
            return Response(
                status_code=401,
                content=b'{"error":{"message":"Unauthorized relay request","type":"relay_auth_error"}}',
                media_type="application/json",
            )

        return await call_next(request)
