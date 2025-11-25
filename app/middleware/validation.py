from __future__ import annotations

import logging
from typing import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger("schema_validation")


class SchemaValidationMiddleware(BaseHTTPMiddleware):
    """
    Lightweight request logger / future hook for schema validation.

    - For GET/HEAD/OPTIONS: pass through without inspecting the body.
    - For other methods: read body once, log payload size, then forward.
    """

    def __init__(self, app: ASGIApp, schema_path: str | None = None) -> None:
        super().__init__(app)
        self.schema_path = schema_path

        if self.schema_path:
            logger.info(
                "SchemaValidationMiddleware enabled with schema: %s",
                self.schema_path,
            )
        else:
            logger.info(
                "SchemaValidationMiddleware enabled (no schema file configured)"
            )

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        # No validation for read-only operations
        if request.method in {"GET", "HEAD", "OPTIONS"}:
            return await call_next(request)

        # Stub for future PDF / OpenAPI-based validation
        try:
            body_bytes = await request.body()
            logger.debug(
                "SchemaValidationMiddleware: %s %s, payload_bytes=%d",
                request.method,
                request.url.path,
                len(body_bytes),
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "SchemaValidationMiddleware: failed to read body for %s %s: %r",
                request.method,
                request.url.path,
                exc,
            )

        return await call_next(request)
