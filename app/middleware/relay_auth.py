from __future__ import annotations

from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse, Response

from app.core.config import settings
from app.utils.authy import check_relay_key


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


class RelayAuthMiddleware(BaseHTTPMiddleware):
    """Relay authentication guard.

    Design intent:
      - Do not require auth for health/openapi/manifest/root.
      - Only gate /v1/* endpoints (the relay surface area).
      - Accept either:
          * X-Relay-Key (or settings.RELAY_AUTH_HEADER) header, or
          * Authorization: Bearer <key>
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        path = request.url.path

        # Public endpoints and static assets.
        if path in _PUBLIC_PATHS or path.startswith("/static/"):
            return await call_next(request)

        if not settings.RELAY_AUTH_ENABLED:
            return await call_next(request)

        # Only guard the relay API surface (v1); allow non-v1 app routes (e.g., landing page).
        if path.startswith("/v1"):
            try:
                check_relay_key(request)
            except HTTPException as exc:
                return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

        return await call_next(request)
