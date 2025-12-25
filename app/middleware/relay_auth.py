from __future__ import annotations

from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import settings


_PUBLIC_PATHS = {
    "/health",
    "/v1/health",
    "/manifest",
    "/openapi.json",
    "/openapi.actions.json",
}


def _extract_relay_key(request: Request) -> Optional[str]:
    # Preferred header
    x_key = request.headers.get("X-Relay-Key")
    if x_key:
        return x_key.strip()

    # Bearer fallback
    auth = request.headers.get("Authorization") or ""
    auth = auth.strip()
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()

    return None


class RelayAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Allow unauthenticated access to public endpoints (health/openapi/manifest).
        if request.url.path in _PUBLIC_PATHS or request.url.path.startswith("/static/"):
            return await call_next(request)

        if not settings.RELAY_AUTH_ENABLED:
            return await call_next(request)

        provided = _extract_relay_key(request)
        if not provided:
            return JSONResponse(status_code=401, content={"detail": "Missing relay key"})

        if provided != settings.RELAY_KEY:
            return JSONResponse(status_code=401, content={"detail": "Invalid relay key"})

        return await call_next(request)
