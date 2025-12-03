# app/middleware/p4_orchestrator.py

from __future__ import annotations

import json
import logging
from typing import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("relay")


class P4OrchestratorMiddleware(BaseHTTPMiddleware):
    """
    Thin placeholder for your P4 Cross-Domain Analogy orchestrator.

    For now it only logs metadata and lets the request flow through.
    This keeps behaviour transparent while giving you a single place
    to later implement more advanced orchestration logic.
    """

    def __init__(
        self,
        app,
        *,
        openai_api_base: str,
        default_model: str,
        realtime_model: str,
        relay_name: str,
    ) -> None:
        super().__init__(app)
        self.openai_api_base = openai_api_base
        self.default_model = default_model
        self.realtime_model = realtime_model
        self.relay_name = relay_name

        logger.info(
            "P4OrchestratorMiddleware initialized",
            extra={
                "openai_api_base": self.openai_api_base,
                "default_model": self.default_model,
                "realtime_model": self.realtime_model,
                "relay_name": self.relay_name,
            },
        )

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        path = request.url.path
        method = request.method

        logger.debug(
            "P4OrchestratorMiddleware dispatch",
            extra={
                "method": method,
                "path": path,
                "default_model": self.default_model,
                "realtime_model": self.realtime_model,
            },
        )

        # In the future you can branch here based on:
        # - path (/v1/responses vs /v1/realtime-calls, etc.)
        # - headers (OpenAI-Beta, client id)
        # - request body (tools, function calls, etc.)
        #
        # For now: just pass through.
        response = await call_next(request)

        # Optional: attach relay metadata header
        response.headers.setdefault("X-Relay-Name", self.relay_name)
        return response
