# app/utils/error_handler.py

from __future__ import annotations

from typing import Any, Dict

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.utils.logger import get_logger

try:
    # These are re-exported by the OpenAI Python SDK 2.x
    from openai import OpenAIError, APIConnectionError, RateLimitError  # type: ignore
except Exception:  # pragma: no cover - SDK may not be installed in some environments
    OpenAIError = Exception  # type: ignore
    APIConnectionError = Exception  # type: ignore
    RateLimitError = Exception  # type: ignore

logger = get_logger()


def _error_payload(exc: Exception, code: int, extra: Dict[str, Any] | None = None) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "error": {
            "type": exc.__class__.__name__,
            "message": str(exc),
        }
    }
    if extra:
        payload["error"].update(extra)
    return payload


def install_exception_handlers(app: FastAPI) -> None:
    """Register shared exception handlers on the FastAPI app."""

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        logger.warning("HTTP error %s on %s %s", exc.status_code, request.method, request.url.path)
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_payload(exc, exc.status_code),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        logger.warning(
            "Request validation failed on %s %s: %s",
            request.method,
            request.url.path,
            exc.errors(),
        )
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "type": "RequestValidationError",
                    "message": "Invalid request payload",
                    "details": exc.errors(),
                }
            },
        )

    @app.exception_handler(RateLimitError)  # type: ignore[misc]
    async def openai_rate_limit_handler(
        request: Request, exc: RateLimitError  # type: ignore[valid-type]
    ) -> JSONResponse:
        logger.warning("OpenAI rate limit exceeded: %s", exc)
        return JSONResponse(
            status_code=429,
            content=_error_payload(exc, 429, {"hint": "Please retry after a short delay."}),
        )

    @app.exception_handler(APIConnectionError)  # type: ignore[misc]
    async def openai_connection_handler(
        request: Request, exc: APIConnectionError  # type: ignore[valid-type]
    ) -> JSONResponse:
        logger.error("OpenAI connection error: %s", exc)
        return JSONResponse(
            status_code=502,
            content=_error_payload(exc, 502, {"hint": "Upstream connection to OpenAI failed."}),
        )

    @app.exception_handler(OpenAIError)  # type: ignore[misc]
    async def openai_generic_handler(
        request: Request, exc: OpenAIError  # type: ignore[valid-type]
    ) -> JSONResponse:
        logger.error("Unhandled OpenAI error: %s", exc)
        return JSONResponse(
            status_code=502,
            content=_error_payload(exc, 502),
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled server error on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=500,
            content=_error_payload(exc, 500, {"hint": "Unexpected server error."}),
        )
