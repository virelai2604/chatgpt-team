from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse

async def forward_openai(request: Request, endpoint: str):
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
    # Add your OpenAI relay logic here
    return JSONResponse(content={"status": "ok", "detail": "Request is valid and ready for relay."})
