# app/middleware/relay_auth.py
from typing import Callable, Awaitable

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.utils.authy import check_relay_key
from app.utils.logger import get_logger

logger = get_logger(__name__)


class RelayAuthMiddleware(BaseHTTPMiddleware):
    """
    Optional shared-secret auth in front of the relay.

    Controlled by:
      - RELAY_KEY (or legacy RELAY_AUTH_TOKEN)
      - RELAY_AUTH_ENABLED (bool, default: True if RELAY_KEY set)

    Exempts:
      - /health
      - /v1/health
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        path = request.url.path

        # Allow health checks without relay auth
        if path in {"/health", "/v1/health"}:
            return await call_next(request)

        auth_header = request.headers.get("Authorization")

        try:
            check_relay_key(auth_header)
        except HTTPException as exc:
            # `exc.detail` already contains the nice structured error payload
            logger.warning(
                "Relay auth failed",
                extra={"path": path, "method": request.method, "detail": exc.detail},
            )
            return JSONResponse(status_code=exc.status_code, content=exc.detail)

        return await call_next(request)
