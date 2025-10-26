# app/utils/error_handler.py — BIFL v2.3.4-fp
import uuid, datetime
from fastapi.responses import JSONResponse

def error_response(error_type: str, message: str, status_code: int = 500):
    """Return standardized error JSON matching OpenAI style."""
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
