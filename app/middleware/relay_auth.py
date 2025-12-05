# app/middleware/relay_auth.py
from typing import Callable, Awaitable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

from ..core.config import get_settings
from ..utils.logger import get_logger

logger = get_logger(__name__)


class RelayAuthMiddleware(BaseHTTPMiddleware):
    """
    Optional shared-secret auth in front of the relay.

    If RELAY_AUTH_TOKEN is set in the environment, every request must include
    an `x-relay-auth` header with the same value.
    """

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        settings = get_settings()
        required_token = settings.relay_auth_token

        if required_token:
            provided = request.headers.get("x-relay-auth")
            if not provided or provided != required_token:
                logger.warning("Rejected request with missing/invalid x-relay-auth header")
                return JSONResponse(status_code=401, content={"detail": "Unauthorized"})

        return await call_next(request)
