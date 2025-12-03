# app/utils/error_handler.py

from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.utils.logger import relay_log

logger = logging.getLogger("relay")


def _error_payload(message: str, *, type_: str = "internal_error", extra: Dict[str, Any] | None = None) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "error": {
            "message": message,
            "type": type_,
        }
    }
    if extra:
        payload["error"].update(extra)
    return payload


def register_exception_handlers(app: FastAPI) -> None:
    """
    Registers a small set of global exception handlers so that any unexpected
    errors still produce OpenAI-style JSON responses.
    """

    @app.exception_handler(StarletteHTTPException)
    async def starlette_http_exception_handler(
        request: Request,
        exc: StarletteHTTPException,
    ) -> JSONResponse:
        relay_log.warning(
            "StarletteHTTPException",
            extra={
                "path": request.url.path,
                "status_code": exc.status_code,
                "detail": str(exc.detail),
            },
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_payload(
                message=str(exc.detail),
                type_="http_error",
                extra={"status_code": exc.status_code},
            ),
        )

    @app.exception_handler(HTTPException)
    async def fastapi_http_exception_handler(
        request: Request,
        exc: HTTPException,
    ) -> JSONResponse:
        relay_log.warning(
            "HTTPException",
            extra={
                "path": request.url.path,
                "status_code": exc.status_code,
                "detail": str(exc.detail),
            },
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_payload(
                message=str(exc.detail),
                type_="http_error",
                extra={"status_code": exc.status_code},
            ),
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        relay_log.exception(
            "Unhandled exception",
            extra={"path": request.url.path},
        )
        return JSONResponse(
            status_code=500,
            content=_error_payload(
                message="Internal relay error",
                type_="internal_error",
            ),
        )
