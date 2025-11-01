# ================================================================
# error_handler.py — Centralized Error Management
# ================================================================
# Provides structured JSON responses for unhandled exceptions and
# application-level errors. Mimics OpenAI's own error schema.
# ================================================================

from fastapi import Request
from fastapi.responses import JSONResponse
import traceback, time, uuid

async def handle_exceptions(request: Request, exc: Exception):
    """
    Global exception handler for FastAPI app.
    Returns JSON structured error matching OpenAI API schema.
    """
    trace_id = f"trace_{uuid.uuid4().hex[:8]}"
    error_message = str(exc)
    error_trace = traceback.format_exc()

    print(f"[ERROR {trace_id}] {error_message}")
    print(error_trace)

    return JSONResponse({
        "error": {
            "message": error_message,
            "type": exc.__class__.__name__,
            "trace_id": trace_id,
            "timestamp": int(time.time())
        }
    }, status_code=500)


def register_exception_handlers(app):
    """
    Attaches error handler to FastAPI app.
    """
    from fastapi.exceptions import RequestValidationError
    from starlette.exceptions import HTTPException

    @app.exception_handler(Exception)
    async def global_handler(request: Request, exc: Exception):
        return await handle_exceptions(request, exc)

    @app.exception_handler(HTTPException)
    async def http_handler(request: Request, exc: HTTPException):
        return JSONResponse({
            "error": {
                "message": exc.detail,
                "status": exc.status_code,
                "type": "http_error"
            }
        }, status_code=exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError):
        return JSONResponse({
            "error": {
                "message": "Validation failed.",
                "details": exc.errors(),
                "type": "validation_error"
            }
        }, status_code=422)

    return app
