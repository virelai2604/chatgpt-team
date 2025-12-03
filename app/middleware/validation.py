# app/middleware/validation.py

from __future__ import annotations

import json
import logging
from json import JSONDecodeError
from typing import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("relay")


class SchemaValidationMiddleware(BaseHTTPMiddleware):
    """
    Lightweight schema/shape validation middleware.

    This does *not* validate against the full OpenAPI spec; it only ensures
    that basic JSON / content-type issues are caught early and turned into
    a well-formed JSON error before they hit the OpenAI proxy.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        # Only inspect methods that usually have bodies
        if request.method not in {"POST", "PUT", "PATCH"}:
            return await call_next(request)

        content_type = request.headers.get("content-type", "").lower()

        try:
            if content_type.startswith("application/json"):
                # Force JSON parsing to catch malformed payloads
                body = await request.body()
                if body.strip():
                    try:
                        json.loads(body)
                    except JSONDecodeError as exc:  # pragma: no cover - explicit branch
                        logger.warning(
                            "Invalid JSON request body",
                            extra={
                                "path": request.url.path,
                                "error": str(exc),
                            },
                        )
                        return Response(
                            status_code=400,
                            content=b'{"error":{"message":"Invalid JSON body","type":"invalid_request_error"}}',
                            media_type="application/json",
                        )
            elif content_type.startswith("multipart/form-data"):
                # Let FastAPI/Starlette deal with it; we just log
                logger.debug(
                    "multipart/form-data request passthrough",
                    extra={"path": request.url.path},
                )
            else:
                # Either empty or some other content type; just log.
                body = await request.body()
                if not body.strip():
                    logger.debug(
                        "Empty request body (no validation applied)",
                        extra={"path": request.url.path},
                    )
                else:
                    logger.debug(
                        "Non-JSON body (no schema validation applied)",
                        extra={
                            "path": request.url.path,
                            "content_type": content_type or "<missing>",
                        },
                    )
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception(
                "Unexpected error during request validation",
                extra={"path": request.url.path},
            )
            # Do not block the request; forward to handler
            return await call_next(request)

        return await call_next(request)
