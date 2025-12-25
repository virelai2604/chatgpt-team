from __future__ import annotations

from typing import Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.utils.authy import check_relay_key


class RelayAuthMiddleware(BaseHTTPMiddleware):
    """
    Enforces an internal "relay key" (client -> relay) for /v1/* endpoints when enabled.
    """

    _PUBLIC_PATHS = {
        "/",
        "/health",
        "/v1/health",
        "/manifest",
        "/v1/manifest",
        "/openapi.json",
        "/openapi.actions.json",
        "/v1/openapi.actions.json",
        "/docs",
        "/redoc",
        "/favicon.ico",
    }

    async def dispatch(self, request: Request, call_next: Callable[[Request], Response]) -> Response:
        path = request.url.path

        if path in self._PUBLIC_PATHS or path.startswith("/static"):
            return await call_next(request)

        if path.startswith("/v1"):
            check_relay_key(request)

        return await call_next(request)
