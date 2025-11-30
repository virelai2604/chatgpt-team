# app/middleware/relay_auth.py

from __future__ import annotations

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.utils.authy import check_relay_key


class RelayAuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware that enforces a relay Authorization header on all
    `/v1/*` and `/relay/*` endpoints, but leaves `/health` public.
    """

    def __init__(self, app: ASGIApp, *, relay_key: str) -> None:
        super().__init__(app)
        self.relay_key = relay_key

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # health endpoints should remain open
        if path not in ("/health", "/v1/health"):
            auth_header = request.headers.get("Authorization")
            check_relay_key(auth_header)

        return await call_next(request)
