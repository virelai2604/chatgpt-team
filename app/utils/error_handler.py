# app/utils/error_handler.py

from __future__ import annotations

from typing import Any, Optional, Type

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from openai._exceptions import OpenAIError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import ClientDisconnect

from app.utils.logger import get_logger

logger = get_logger(__name__)

# Non-standard but widely used by proxies (e.g., nginx) to signal "Client Closed Request".
CLIENT_CLOSED_REQUEST_STATUS = 499


def _base_error_payload(
    message: str,
    status: int,
    code: Optional[str] = None,
) -> dict[str, Any]:
    return {
        "error": {
            "message": message,
            "type": "relay_error",
            "param": None,
            "code": code,
        },
        "status": status,
    }


# ExceptionGroup exists in Python 3.11+
try:
    ExceptionGroupType: Optional[Type[BaseException]] = ExceptionGroup  # type: ignore[name-defined]
except NameError:  # pragma: no cover
    ExceptionGroupType = None


def _is_client_disconnect(exc: BaseException) -> bool:
    """
    Return True if:
      - exc is ClientDisconnect, OR
      - exc is an ExceptionGroup where *every* inner exception is a ClientDisconnect.
    """
    if isinstance(exc, ClientDisconnect):
        return True

    if ExceptionGroupType is not None and isinstance(exc, ExceptionGroupType):
        try:
            # ExceptionGroup exposes `.exceptions` (tuple of underlying exceptions)
            inner = exc.exceptions  # type: ignore[attr-defined]
            return all(_is_client_disconnect(e) for e in inner)
        except Exception:
            return False

    return False


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        logger.warning("HTTP error", extra={"status_code": exc.status_code, "detail": exc.detail})
        return JSONResponse(
            status_code=exc.status_code,
            content=_base_error_payload(str(exc.detail), exc.status_code),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.warning("Validation error", extra={"errors": exc.errors()})
        return JSONResponse(
            status_code=422,
            content=_base_error_payload("Validation error", 422),
        )

    @app.exception_handler(OpenAIError)
    async def openai_exception_handler(request: Request, exc: OpenAIError):
        logger.error("OpenAI API error", extra={"error": str(exc)})
        return JSONResponse(
            status_code=502,
            content=_base_error_payload(f"Upstream OpenAI error: {exc}", 502),
        )

    @app.exception_handler(ClientDisconnect)
    async def client_disconnect_handler(request: Request, exc: ClientDisconnect):
        # Client closed connection mid-request. This is not a server bug; do not log as ERROR.
        logger.info(
            "Client disconnected",
            extra={"method": request.method, "path": request.url.path},
        )
        return JSONResponse(
            status_code=CLIENT_CLOSED_REQUEST_STATUS,
            content=_base_error_payload("Client disconnected", CLIENT_CLOSED_REQUEST_STATUS),
        )

    if ExceptionGroupType is not None:

        @app.exception_handler(ExceptionGroupType)  # type: ignore[arg-type]
        async def exception_group_handler(request: Request, exc: BaseException):
            # Starlette/AnyIO may wrap disconnects inside an ExceptionGroup.
            if _is_client_disconnect(exc):
                logger.info(
                    "Client disconnected (exception group)",
                    extra={"method": request.method, "path": request.url.path},
                )
                return JSONResponse(
                    status_code=CLIENT_CLOSED_REQUEST_STATUS,
                    content=_base_error_payload("Client disconnected", CLIENT_CLOSED_REQUEST_STATUS),
                )

            logger.exception("Unhandled exception group")
            return JSONResponse(
                status_code=500,
                content=_base_error_payload("Internal Server Error", 500),
            )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        # Defensive fallback: in case a disconnect slips through as a generic Exception.
        if _is_client_disconnect(exc):
            logger.info(
                "Client disconnected (caught by generic handler)",
                extra={"method": request.method, "path": request.url.path},
            )
            return JSONResponse(
                status_code=CLIENT_CLOSED_REQUEST_STATUS,
                content=_base_error_payload("Client disconnected", CLIENT_CLOSED_REQUEST_STATUS),
            )

        logger.exception("Unhandled server error")
        return JSONResponse(
            status_code=500,
            content=_base_error_payload("Internal Server Error", 500),
        )
