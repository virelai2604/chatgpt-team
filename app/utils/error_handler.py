from fastapi.responses import JSONResponse

def error_response(error_type, message, status_code=400):
    return JSONResponse(
        content={'error': {'type': error_type, 'message': message}},
        status_code=status_code
    )
