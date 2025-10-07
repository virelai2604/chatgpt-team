from fastapi.responses import JSONResponse

def error_response(error_type: str, message: str, status_code: int = 400, detail: dict = None):
    body = {
        "error": {
            "type": error_type,
            "message": message,
            "detail": detail or {}
        }
    }
    return JSONResponse(content=body, status_code=status_code)
