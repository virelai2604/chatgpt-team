from __future__ import annotations

import logging
from pathlib import Path
from typing import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger("schema_validation")

# Project root (repo root) – app/middleware/validation.py → app → <root>
PROJECT_ROOT = Path(__file__).resolve().parents[2]


class SchemaValidationMiddleware(BaseHTTPMiddleware):
    """
    Lightweight request logger and schema hook for the relay.

    Current responsibilities:
      - Wire the validation schema PDF path (from settings/env) into the app.
      - Resolve the file relative to the project root and log its existence.
      - Log payload sizes for write operations while always forwarding requests.

    Future responsibilities (next step):
      - Use the PDF + live OpenAI docs to enforce method/path contracts and
        request-shape validation for OpenAI-compatible endpoints.
    """

    def __init__(
        self,
        app: ASGIApp,
        schema_path: str | None = None,
        **_: object,  # absorb any extra kwargs FastAPI might pass
    ) -> None:
        # BaseHTTPMiddleware only expects (app, dispatch) – do NOT pass schema_path.
        super().__init__(app)

        self.schema_path_raw: str | None = schema_path
        self.schema_path: Path | None = None
        self.schema_available: bool = False

        if schema_path:
            candidate = Path(schema_path)
            if not candidate.is_absolute():
                candidate = PROJECT_ROOT / candidate

            self.schema_path = candidate
            self.schema_available = candidate.exists()

            if self.schema_available:
                logger.info(
                    "SchemaValidationMiddleware enabled with schema: %s",
                    self.schema_path,
                )
            else:
                logger.warning(
                    (
                        "SchemaValidationMiddleware configured with schema '%s', "
                        "but no file exists at resolved path: %s"
                    ),
                    schema_path,
                    self.schema_path,
                )
        else:
            logger.info(
                "SchemaValidationMiddleware enabled (no schema file configured)",
            )

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """
        For now, behave as a tolerant logger:

        - Read-only methods (GET/HEAD/OPTIONS) are passed through untouched.
        - Write methods log payload size, then the request is forwarded unchanged.

        This keeps behavior safe while still wiring the schema path into the
        runtime, ready for future contract enforcement.
        """
        # No validation / body inspection for read-only operations
        if request.method in {"GET", "HEAD", "OPTIONS"}:
            return await call_next(request)

        # Stub for future schema/OpenAPI-based validation
        try:
            body_bytes = await request.body()
            logger.debug(
                "SchemaValidationMiddleware: %s %s, payload_bytes=%d, schema_available=%s",
                request.method,
                request.url.path,
                len(body_bytes),
                self.schema_available,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "SchemaValidationMiddleware: failed to read body for %s %s: %r",
                request.method,
                request.url.path,
                exc,
            )

        # Important: always forward the request, even if logging fails
        return await call_next(request)
