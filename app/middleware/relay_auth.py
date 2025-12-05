# app/middleware/relay_auth.py

from __future__ import annotations

import logging

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.utils.authy import check_relay_key

logger = logging.getLogger("relay.auth")

SAFE_PATH_PREFIXES = (
    "/health",
    "/v1/health",
    "/openapi.json",
    "/docs",
    "/redoc",
)


class RelayAuthMiddleware(BaseHTTPMiddleware):
    """
    Simple Bearer-based auth for the relay itself.

    - Enabled when settings.RELAY_AUTH_ENABLED is true.
    - Expects Authorization: Bearer <RELAY_KEY>.
    - Skips health and documentation endpoints.
    """

    async def dispatch(self, request: Request, call_next):
        if not settings.RELAY_AUTH_ENABLED:
            return await call_next(request)

        path = request.url.path

        # Allow health/docs/metadata without auth
        if path.startswith(SAFE_PATH_PREFIXES):
            return await call_next(request)

        auth_header = request.headers.get("Authorization")

        # Raises HTTPException(401) on failure; FastAPI will convert to JSON error
        check_relay_key(auth_header)

        logger.debug("Relay auth ok for %s", path)
        return await call_next(request)
