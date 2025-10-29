# ==========================================================
# app/routes/realtime.py — Ground Truth OpenAI-Compatible Mirror
# ==========================================================
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from app.api.forward_openai import forward_openai_request
import httpx

router = APIRouter(prefix="/v1/realtime", tags=["Realtime"])

@router.post("/sessions")
async def create_realtime_session(request: Request):
    """
    Mirrors OpenAI POST /v1/realtime/sessions
    Creates a new realtime session token or configuration object.
    """
    try:
        body = await request.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}")

    try:
        result = await forward_openai_request(
            "v1/realtime/sessions",
            method="POST",
            json_data=body,
        )
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upstream relay error: {e}")

    return JSONResponse(result)
