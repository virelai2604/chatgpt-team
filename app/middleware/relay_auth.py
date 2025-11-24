from __future__ import annotations

from typing import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.utils.authy import RELAY_AUTH_ENABLED, check_relay_key

PUBLIC_PATHS = {
    "/health",
    "/v1/health",
    "/actions/ping",
    "/actions/relay_info",
    "/v1/actions/relay_info",
}


def _is_public_path(path: str) -> bool:
    return path in PUBLIC_PATHS


def _is_protected_v1_path(path: str) -> bool:
    if not path.startswith("/v1/"):
        return False
    if path == "/v1/health":
        return False
    return True


class RelayAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if not RELAY_AUTH_ENABLED:
            return await call_next(request)

        path = request.url.path

        if _is_public_path(path):
            return await call_next(request)

        if _is_protected_v1_path(path):
            auth_header = request.headers.get("Authorization")
            check_relay_key(auth_header)

        return await call_next(request)
