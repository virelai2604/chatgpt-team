# app/utils/error_handler.py — BIFL v2.3.3
from fastapi.responses import JSONResponse
from datetime import datetime
import uuid, asyncio

async def _log_error(body):
    try:
        from app.utils.db_logger import save_raw_request
        await asyncio.to_thread(save_raw_request, "internal/error", str(body), "{}")
    except Exception as e:
        print(f"[BIFL ERROR HANDLER] Logging failed: {e}")

def error_response(error_type: str, message: str, status_code: int = 400, detail: dict = None, log_to_db: bool = False):
    """Return standardized error JSON with trace and version."""
    trace_id = str(uuid.uuid4())
    body = {
        "error": {
            "type": error_type,
            "message": message,
            "detail": detail or {},
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "trace_id": trace_id,
            "bifl_version": "2.3.3"
        }
    }
    if log_to_db:
        asyncio.create_task(_log_error(body))
    return JSONResponse(content=body, status_code=status_code)
