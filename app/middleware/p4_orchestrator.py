from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable, Dict

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger("p4_orchestrator")

CORE_ENDPOINT_PREFIXES = (
    "/v1/responses",
    "/v1/embeddings",
    "/v1/models",
    "/v1/files",
    "/v1/vector_stores",
    "/v1/conversations",
    "/v1/images",
    "/v1/videos",
    "/v1/realtime",
    "/relay/actions",
    "/relay/models",
)


class P4OrchestratorMiddleware(BaseHTTPMiddleware):
    """
    P4 orchestration hook.

    For now, this is a safe pass-through middleware:
    - Accepts arbitrary config (OpenAI base, models, timeouts, etc.).
    - Logs traffic for core AI endpoints.
    - Forwards requests to downstream routes without modification.
    """

    def __init__(self, app: ASGIApp, **config: Any) -> None:
        super().__init__(app)
        self.config: Dict[str, Any] = dict(config)
        logger.info(
            "P4OrchestratorMiddleware initialized (config keys: %s)",
            ", ".join(self.config.keys()) or "none",
        )

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        path = request.url.path
        method = request.method

        if path.startswith(CORE_ENDPOINT_PREFIXES):
            logger.debug("P4 orchestrator passthrough: %s %s", method, path)

        # Future: inject orchestration, tracing, cross-domain flows here.
        response = await call_next(request)
        return response
