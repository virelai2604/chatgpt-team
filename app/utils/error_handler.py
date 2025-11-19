"""
error_handler.py — Global Exception and Error Registration
───────────────────────────────────────────────────────────
Handles unexpected exceptions and registers FastAPI error events.

The error payload format follows the OpenAI API convention:

    {
        "error": {
            "message": "...",
            "type": "invalid_request_error | server_error | ...",
            "param": "optional_param_name_or_null",
            "code": "optional_machine_readable_code_or_null"
        }
    }

This keeps the relay compatible with openai-python 2.x and other
OpenAI-compatible SDKs that expect this schema.
"""

import logging
import os
import traceback
from typing import Any, Dict, Optional

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("relay")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_ENV = os.getenv("ENVIRONMENT", "").lower()
_APP_MODE = os.getenv("APP_MODE", "").lower()
_DEBUG = _ENV in {"dev", "development", "local", "test"} or _APP_MODE in {
    "dev",
    "development",
    "local",
    "test",
}


def _openai_error_body(
    *,
    message: str,
    err_type: str,
    status_code: int,
    param: Optional[str] = None,
    code: Optional[str] = None,
    request: Optional[Request] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Build an OpenAI-style error envelope.

    OpenAI APIs typically wrap errors as:

        HTTP 4xx/5xx
        {
          "error": {
            "message": "...",
            "type": "invalid_request_error",
            "param": "messages[0].content",
            "code": "invalid_type"
          }
        }
    """
    error_obj: Dict[str, Any] = {
        "message": message,
        "type": err_type,
        "param": param,
        "code": code,
    }

    if request is not None:
        # Non-standard but helpful for debugging on the client side
        error_obj["path"] = str(request.url)

    if extra:
        # Namespaced to avoid clashing with core fields
        error_obj["extra"] = extra

    body = {"error": error_obj}

    if _DEBUG:
        body["debug"] = {
            "status_code": status_code,
        }

    return body


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


def register_exception_handlers(app: FastAPI) -> None:
    """
    Attach global exception handlers to the FastAPI app.

    This is intended to be called exactly once during app startup
    (typically from app.main).
    """

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        status = exc.status_code
        detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)

        if status >= 500:
            err_type = "server_error"
            code = f"http_{status}"
            log_method = logger.error
        else:
            err_type = "invalid_request_error"
            code = f"http_{status}"
            log_method = logger.warning

        log_method(
            "HTTPException in relay",
            extra={"path": str(request.url), "status_code": status},
        )

        body = _openai_error_body(
            message=detail or "Request failed.",
            err_type=err_type,
            status_code=status,
            param=None,
            code=code,
            request=request,
            extra={"detail": detail},
        )
        return JSONResponse(status_code=status, content=body)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        status = 422
        logger.warning(
            "Request validation error",
            extra={"path": str(request.url), "status_code": status},
        )

        body = _openai_error_body(
            message="Request validation failed.",
            err_type="invalid_request_error",
            status_code=status,
            param=None,
            code="validation_error",
            request=request,
            extra={"errors": exc.errors()},
        )
        return JSONResponse(status_code=status, content=body)

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        status = 500
        logger.exception(
            "Unhandled exception in relay",
            extra={"path": str(request.url), "status_code": status},
        )

        tb_str = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))

        message = "An unexpected error occurred on the relay."
        body = _openai_error_body(
            message=message,
            err_type="server_error",
            status_code=status,
            param=None,
            code="internal_error",
            request=request,
            extra={"exception": str(exc)},
        )

        if _DEBUG:
            # In dev/local environments, include a short trace for easier debugging
            lines = tb_str.splitlines()
            body.setdefault("debug", {})["trace_tail"] = lines[-10:]

        return JSONResponse(status_code=status, content=body)