"""
error_handler.py — Global Exception and Error Registration
───────────────────────────────────────────────────────────
Handles unexpected exceptions and registers FastAPI error events.
"""

import logging
import os
import traceback

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("relay")

# Determine whether we are running in a debug-like environment
_ENV = os.getenv("ENVIRONMENT") or os.getenv("APP_MODE") or "production"
_DEBUG = _ENV.lower() in ("development", "dev", "local", "debug")


def register_error_handlers(app: FastAPI):
    """
    Attach global exception handlers to the FastAPI app.
    """

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        logger.warning(
            "HTTP error %s on %s: %s",
            exc.status_code,
            request.url.path,
            exc.detail,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "type": "http_error",
                    "message": exc.detail,
                    "path": str(request.url),
                }
            },
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        tb = traceback.format_exc()
        logger.error(
            "Unhandled server error on %s: %s\n%s",
            request.url.path,
            str(exc),
            tb,
        )

        # In production, do not expose internal stack traces
        base_content = {
            "error": {
                "type": "server_error",
                "message": "An unexpected error occurred on the relay.",
                "path": str(request.url),
            }
        }

        if _DEBUG:
            # In dev/local environments, include a short trace for easier debugging
            base_content["error"]["debug_detail"] = {
                "exception": str(exc),
                "trace_tail": tb.splitlines()[-5:],
            }

        return JSONResponse(status_code=500, content=base_content)
