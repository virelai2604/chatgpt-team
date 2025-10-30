# ==========================================================
# app/utils/error_handler.py — Ground Truth Error Wrapper
# ==========================================================
import datetime
import uuid
from fastapi import Request
from fastapi.responses import JSONResponse


def register_error_handlers(app):
    @app.exception_handler(Exception)
    async def handle_exception(request: Request, exc: Exception):
        error_id = str(uuid.uuid4())
        return JSONResponse(
            {
                "error": {
                    "type": "internal_error",
                    "message": str(exc),
                    "trace_id": error_id,
                    "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
                }
            },
            status_code=500,
        )

    return app
