# app/middleware/p4_orchestrator.py
import uuid
from typing import Callable, Awaitable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from ..utils.logger import get_logger

logger = get_logger(__name__)


class P4OrchestratorMiddleware(BaseHTTPMiddleware):
    """
    Simple correlation-ID and request logging middleware aligned with the P4 orchestration idea.
    """

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
        request.state.request_id = request_id

        logger.info(
            "Incoming request",
            extra={"path": str(request.url), "method": request.method, "request_id": request_id},
        )

        response = await call_next(request)
        response.headers["x-request-id"] = request_id
        return response
