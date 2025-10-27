# ==========================================================
# app/utils/error_handler.py — BIFL v2.3.4-fp
# ==========================================================
# Centralized JSON error handler for all relay endpoints.
# Converts any raised exception into OpenAI-compatible JSON.
# Automatically decodes bytes, bytearrays, and non-serializable data.
# ==========================================================

import uuid
import datetime
from fastapi.responses import JSONResponse

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
