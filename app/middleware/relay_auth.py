from __future__ import annotations

from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import settings
from app.utils.logger import relay_log as logger


def _is_public_path(path: str) -> bool:
    # Always-public health & docs/bootstrap endpoints
    if path in {"/", "/health", "/v1/health"}:
        return True
    if path in {"/openapi.json", "/docs", "/redoc", "/manifest"}:
        return True
    # Actions helper endpoints are usually safe to keep public.
    if path.startswith("/v1/actions/"):
        return True
    return False


def _valid_tokens() -> set[str]:
    """
    Tokens that should be accepted for relay authentication.

    Primary token: settings.RELAY_KEY
    Optional token: settings.RELAY_AUTH_TOKEN (if present)
    """
    tokens: set[str] = set()
    relay_key = getattr(settings, "RELAY_KEY", "") or ""
    auth_token = getattr(settings, "RELAY_AUTH_TOKEN", "") or ""
    if relay_key:
        tokens.add(relay_key)
    if auth_token:
        tokens.add(auth_token)
    return tokens


def _extract_bearer_token(authorization: str) -> Optional[str]:
    parts = authorization.split(None, 1)
    if len(parts) != 2:
        return None
    scheme, token = parts[0], parts[1]
    if scheme.lower() != "bearer":
        return None
    token = token.strip()
    return token or None


class RelayAuthMiddleware(BaseHTTPMiddleware):
    """
    Gateway-style auth guard.

    Key behavior:
    - Middleware is installed unconditionally in app/main.py.
    - Enforcement is conditional at request-time:
        settings.RELAY_AUTH_ENABLED and (RELAY_KEY or RELAY_AUTH_TOKEN)

    This supports tests that monkeypatch settings without rebuilding the ASGI app.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path

        if _is_public_path(path):
            return await call_next(request)

        # Only enforce when explicitly enabled.
        if not bool(getattr(settings, "RELAY_AUTH_ENABLED", False)):
            return await call_next(request)

        allowed_tokens = _valid_tokens()
        if not allowed_tokens:
            logger.warning("Relay auth enabled but no RELAY_KEY/RELAY_AUTH_TOKEN set; allowing request.")
            return await call_next(request)

        # Scope: protect /v1/* by default
        if not path.startswith("/v1/"):
            return await call_next(request)

        # Accept either X-Relay-Key or Authorization: Bearer <token>
        x_relay_key = request.headers.get("x-relay-key")
        if x_relay_key and x_relay_key in allowed_tokens:
            return await call_next(request)

        authorization = request.headers.get("authorization")
        if authorization:
            token = _extract_bearer_token(authorization)
            if token is None:
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Authorization header must be 'Bearer <token>'."},
                )
            if token not in allowed_tokens:
                return JSONResponse(status_code=401, content={"detail": "Invalid relay key."})
            return await call_next(request)

        return JSONResponse(status_code=401, content={"detail": "Missing relay key."})
