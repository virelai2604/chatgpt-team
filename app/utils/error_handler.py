# app/utils/error_handler.py
from typing import Any, Dict

import openai
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .logger import get_logger

logger = get_logger(__name__)


def _base_error_payload(message: str, extra: Dict[str, Any] | None = None) -> Dict[str, Any]:
    payload: Dict[str, Any] = {"detail": message}
    if extra:
        payload.update(extra)
    return payload


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.warning(
            "Request validation error",
            extra={"path": str(request.url), "errors": exc.errors()},
        )
        return JSONResponse(
            status_code=422,
            content=_base_error_payload("Validation error", {"errors": exc.errors()}),
        )

    @app.exception_handler(openai.APITimeoutError)
    async def openai_timeout_handler(request: Request, exc: openai.APITimeoutError):
        logger.error("OpenAI request timed out", exc_info=exc)
        return JSONResponse(
            status_code=504,
            content=_base_error_payload("Upstream OpenAI request timed out"),
        )

    @app.exception_handler(openai.APIStatusError)
    async def openai_status_handler(request: Request, exc: openai.APIStatusError):
        logger.error(
            "OpenAI API status error",
            extra={"status_code": exc.status_code, "request_id": exc.request_id},
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=_base_error_payload(
                exc.message,
                {"request_id": exc.request_id, "status_code": exc.status_code},
            ),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        logger.warning(
            "HTTP error",
            extra={"status_code": exc.status_code, "detail": exc.detail},
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=_base_error_payload(str(exc.detail)),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled server error")
        return JSONResponse(
            status_code=500,
            content=_base_error_payload("Internal server error"),
        )
