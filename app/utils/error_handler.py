"""
error_handler.py — Global Exception and Error Registration
───────────────────────────────────────────────────────────
Handles unexpected exceptions and registers FastAPI error events.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
import traceback


def register_error_handlers(app: FastAPI):
    """
    Attach global exception handlers to the FastAPI app.
    """

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "type": "http_error",
                    "message": exc.detail,
                    "path": str(request.url)
                }
            },
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        tb = traceback.format_exc()
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "type": "server_error",
                    "message": str(exc),
                    "trace": tb.splitlines()[-5:],
                    "path": str(request.url)
                }
            },
        )
