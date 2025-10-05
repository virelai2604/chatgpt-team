from fastapi import Request
from fastapi.responses import JSONResponse

async def forward_openai(request: Request, endpoint: str):
    # Only require body for POST, PUT, PATCH
    if request.method in ["POST", "PUT", "PATCH"]:
        body = await request.body()
        if not body:
            return JSONResponse(
                content={"error": {"type": "bad_request", "message": "Missing request body"}},
                status_code=400
            )
        try:
            json_body = await request.json()
        except Exception as e:
            return JSONResponse(
                content={"error": {"type": "bad_request", "message": f"Invalid JSON body: {str(e)}"}},
                status_code=400
            )
        # Here you would forward json_body to OpenAI if needed

    # For GET, DELETE, OPTIONS, etc: do not require body, just forward as is
    # Here you would forward request to OpenAI if needed

    # Placeholder: For now, just return status
    return JSONResponse(content={"status": "ok", "detail": "Request is valid and ready for relay."})
