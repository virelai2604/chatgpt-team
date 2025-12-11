# app/middleware/relay_auth.py

from __future__ import annotations

from typing import Awaitable, Callable

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.utils.authy import check_relay_key
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Exact paths that should always be public
SAFE_EXACT_PATHS = {
    "/",  # root
    "/health",
    "/health/",
    "/v1/health",
    "/v1/health/",
    "/actions/ping",
    "/actions/relay_info",
    "/v1/actions/ping",
    "/v1/actions/relay_info",
}

# Prefixes that should always be public (docs, openapi, assets, etc.)
SAFE_PREFIXES = (
    "/docs",
    "/redoc",
    "/openapi.json",
    "/static",
    "/favicon",
)


class RelayAuthMiddleware(BaseHTTPMiddleware):
    """
    Optional shared-secret auth in front of the relay.

    Controlled by env / settings:

      - RELAY_KEY (or legacy RELAY_AUTH_TOKEN)
      - RELAY_AUTH_ENABLED (bool)

    Behavior:

      - Health + docs + actions ping/info are always public.
      - Non-/v1/ paths remain public.
      - /v1/* paths are protected when RELAY_AUTH_ENABLED is True.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        path = request.url.path

        # Public routes
        if path in SAFE_EXACT_PATHS or path.startswith(SAFE_PREFIXES):
            return await call_next(request)

        # Only protect OpenAI-style API paths under /v1
        if not path.startswith("/v1/"):
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        x_relay_key = request.headers.get("X-Relay-Key")

        try:
            # Will no-op if RELAY_AUTH_ENABLED is False
            check_relay_key(auth_header=auth_header, x_relay_key=x_relay_key)
        except HTTPException as exc:
            # DO NOT let this bubble out as an exception to httpx;
            # convert to a normal JSON error response.
            logger.warning(
                "Relay auth failed",
                extra={"path": path, "method": request.method, "detail": exc.detail},
            )
            return JSONResponse(
                status_code=exc.status_code,
                content={"detail": exc.detail},
                headers=getattr(exc, "headers", None) or {},
            )

        # Auth OK (or disabled)
        return await call_next(request)
