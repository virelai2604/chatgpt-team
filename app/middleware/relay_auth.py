from __future__ import annotations

from typing import Callable, Awaitable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.utils.authy import RELAY_AUTH_ENABLED, check_relay_key


# Public endpoints that should NOT require RELAY_KEY even when
# RELAY_AUTH_ENABLED is true. Adjust this list to taste.
PUBLIC_PATHS = {
    "/health",
    "/v1/health",
    "/actions/ping",
    "/actions/relay_info",
    "/v1/actions/relay_info",
}


def _is_public_path(path: str) -> bool:
    if path in PUBLIC_PATHS:
        return True
    # Add any additional patterns here if needed.
    return False


def _is_protected_v1_path(path: str) -> bool:
    """
    Decide which /v1/* routes should require RELAY_KEY when
    RELAY_AUTH_ENABLED is true.

    You can tune this list if you want some /v1/* surfaces to remain
    open in certain deployments.
    """
    if not path.startswith("/v1/"):
        return False

    # v1 health is explicitly public above
    if path == "/v1/health":
        return False

    # By default, treat all /v1/* as protected unless explicitly excluded.
    return True


class RelayAuthMiddleware(BaseHTTPMiddleware):
    """
    Central RELAY_KEY auth gate.

    - If RELAY_AUTH_ENABLED is false:
        → Pass through; no auth enforced.

    - Else:
        → For PUBLIC_PATHS: pass through.
        → For /v1/* paths (except explicit exclusions):
              check Authorization header via check_relay_key().
        → For all other paths: pass through.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if not RELAY_AUTH_ENABLED:
            # Auth globally disabled (e.g., ChatGPT Action env)
            return await call_next(request)

        path = request.url.path

        if _is_public_path(path):
            return await call_next(request)

        if _is_protected_v1_path(path):
            auth_header = request.headers.get("Authorization")
            # This may raise HTTPException 401/500, which FastAPI will
            # render using your global error handlers.
            check_relay_key(auth_header)

        return await call_next(request)
