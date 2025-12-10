# app/middleware/relay_auth.py
from typing import Callable, Awaitable

from fastapi import HTTPException, Request
from fastapi.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.utils.authy import check_relay_key
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Exact paths that should *never* require relay auth
SAFE_EXACT_PATHS = {
    "/",  # root stays public in tests
    "/health",
    "/health/",
    "/v1/health",
    "/v1/health/",
    "/actions/ping",
    "/actions/relay_info",
    "/v1/actions/ping",
    "/v1/actions/relay_info",
}

# Prefixes that should stay public (docs, OpenAPI, static assets, etc.)
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

    Controlled by:

      - RELAY_KEY (or legacy RELAY_AUTH_TOKEN)
      - RELAY_AUTH_ENABLED (bool, default: True if RELAY_KEY set)

    Behavior (matching tests):

      - Health endpoints and actions ping/relay_info are always public.
      - Docs and OpenAPI are always public.
      - Non-/v1/ routes remain public.
      - /v1/* routes are protected when RELAY_AUTH_ENABLED is True.
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

        try:
            # This will no-op if RELAY_AUTH_ENABLED is False, per settings
            check_relay_key(auth_header)
        except HTTPException as exc:
            # Log and re-raise so FastAPI produces {"detail": "<string>"}
            logger.warning(
                "Relay auth failed",
                extra={"path": path, "method": request.method, "detail": exc.detail},
            )
            raise

        return await call_next(request)
