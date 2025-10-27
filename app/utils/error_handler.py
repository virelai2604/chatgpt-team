# ==========================================================
# app/utils/error_handler.py — BIFL v2.3.4-fp
# ==========================================================
# Centralized JSON error handler for all relay endpoints.
# Converts any raised exception into OpenAI-compatible JSON.
# Automatically decodes bytes, bytearrays, and non-serializable data.
# Also includes register_error_handlers(app) for FastAPI integration.
# ==========================================================

import uuid
import datetime
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException

# ----------------------------------------------------------
# 🌐 Core JSON Error Response
# ----------------------------------------------------------
def error_response(error_type: str, message, status_code: int = 500):
    """Return standardized JSON error, OpenAI-compatible."""

    # --- Universal serialization guard ---
    if isinstance(message, (bytes, bytearray)):
        try:
            message = message.decode("utf-8", errors="replace")
        except Exception:
            message = str(message)

    # Some exceptions may include embedded objects
    if not isinstance(message, str):
        try:
            message = str(message)
        except Exception:
            message = "<unserializable error>"

    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "type": error_type,
                "message": message,
                "detail": {},
                "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
                "trace_id": str(uuid.uuid4()),
                "bifl_version": "2.3.4-fp",
            }
        },
    )


# ----------------------------------------------------------
# 🧩 Register Global Exception Handlers
# ----------------------------------------------------------
def register_error_handlers(app: FastAPI):
    """
    Attach consistent JSON error handling to the FastAPI app.
    Ensures all HTTP, validation, and uncaught exceptions return
    OpenAI-style JSON envelopes instead of default HTML responses.
    """

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return error_response("http_error", exc.detail, exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return error_response("validation_error", str(exc), 422)

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        msg = str(exc)
        if isinstance(exc, (bytes, bytearray)):
            try:
                msg = exc.decode("utf-8", errors="replace")
            except Exception:
                msg = str(exc)
        return error_response("internal_error", msg, 500)
