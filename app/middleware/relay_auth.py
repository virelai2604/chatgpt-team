from __future__ import annotations

from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import settings


# Paths that should remain reachable without relay auth:
# - health checks
# - OpenAPI + manifest (ChatGPT Actions)
# - docs (optional)
_PUBLIC_PATHS = {
    "/",
    "/health",
    "/v1/health",
    "/manifest",
    "/openapi.json",
    "/openapi.actions.json",
    "/docs",
    "/redoc",
}


def _extract_relay_key(request: Request) -> Optional[str]:
    # Preferred header
    x_key = request.headers.get("X-Relay-Key")
    if x_key:
        return x_key.strip()

    # Bearer fallback
    auth = (request.headers.get("Authorization") or "").strip()
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()

    return None


class RelayAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Public endpoints (no auth).
        if request.url.path in _PUBLIC_PATHS or request.url.path.startswith("/static/"):
            return await call_next(request)

        # If auth is disabled, do nothing.
        if not settings.RELAY_AUTH_ENABLED:
            return await call_next(request)

        # If Authorization exists but is not Bearer, return a message that includes "Bearer"
        # (tests assert this).
        auth = (request.headers.get("Authorization") or "").strip()
        if auth and not auth.lower().startswith("bearer "):
            return JSONResponse(
                status_code=401,
                content={"detail": "Authorization must be Bearer <relay_key> (or use X-Relay-Key)."},
            )

        provided = _extract_relay_key(request)
        if not provided:
            return JSONResponse(status_code=401, content={"detail": "Missing relay key"})

        if provided != settings.RELAY_KEY:
            return JSONResponse(status_code=401, content={"detail": "Invalid relay key"})

        return await call_next(request)
