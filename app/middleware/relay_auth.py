from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import settings
from app.utils.authy import check_relay_key
from app.utils.logger import relay_log as logger

# These paths should remain reachable even when RELAY_AUTH_ENABLED=true.
SAFE_PATHS: set[str] = {
    "/",
    "/health",
    "/v1/health",
    "/manifest",
    "/v1/manifest",
    "/openapi.actions.json",
    "/openapi.json",
    "/docs",
    "/redoc",
}

# Prefix matches for static assets (docs, etc.)
SAFE_PREFIXES: tuple[str, ...] = (
    "/docs",
    "/redoc",
    "/static",
)


class RelayAuthMiddleware(BaseHTTPMiddleware):
    """
    Request-time relay auth enforcement.

    This middleware is ALWAYS installed; whether it enforces auth is controlled by settings flags
    evaluated at request time (so tests can monkeypatch settings without rebuilding the app).
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        # Allow CORS preflight without auth.
        if request.method.upper() == "OPTIONS":
            return await call_next(request)

        path = request.url.path

        if path in SAFE_PATHS or any(path.startswith(p) for p in SAFE_PREFIXES):
            return await call_next(request)

        if bool(getattr(settings, "RELAY_AUTH_ENABLED", False)) and str(getattr(settings, "RELAY_KEY", "") or ""):
            try:
                check_relay_key(
                    auth_header=request.headers.get("authorization"),
                    x_relay_key=request.headers.get("x-relay-key"),
                )
            except Exception as e:
                # Preserve exact detail/status via the HTTPException thrown by check_relay_key.
                logger.info("Relay auth blocked request %s %s: %s", request.method, path, e)
                raise

        return await call_next(request)
