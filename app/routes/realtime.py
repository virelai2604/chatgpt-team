# ==========================================================
# app/routes/realtime.py — Ground Truth Edition (2025.10)
# ==========================================================
"""
Implements all realtime endpoints in OpenAI's 2025.10 spec:
  - /v1/realtime/models
  - /v1/realtime/sessions
  - /v1/realtime/events (POST + GET)

Handles session creation, event dispatch, and SSE streaming.
Forwards directly to OpenAI upstream through the shared
forward_openai_request() proxy layer.
"""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from app.api.forward_openai import forward_openai_request

router = APIRouter(tags=["Realtime"])


# ----------------------------------------------------------
# GET /v1/realtime/models
# ----------------------------------------------------------
@router.get("/v1/realtime/models")
async def list_realtime_models():
    """
    List all realtime-capable models supported by OpenAI.
    Returns 501 if realtime endpoints are unavailable upstream.
    """
    try:
        return await forward_openai_request("v1/realtime/models", method="GET")
    except Exception:
        # OpenAI currently returns 404 for unsupported realtime endpoints.
        # The Ground Truth edition standardizes this as a graceful 501.
        return JSONResponse(
            content={"object": "list", "data": [], "warning": "realtime models unavailable"},
            status_code=501
        )


# ----------------------------------------------------------
# POST /v1/realtime/sessions
# ----------------------------------------------------------
@router.post("/v1/realtime/sessions")
async def create_realtime_session(request: Request):
    """
    Creates a new realtime session configuration for GPT-4o models.
    Mirrors the OpenAI realtime session creation API.
    """
    body = await request.json()
    try:
        return await forward_openai_request("v1/realtime/sessions", method="POST", json=body)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


# ----------------------------------------------------------
# POST /v1/realtime/events
# ----------------------------------------------------------
@router.post("/v1/realtime/events")
async def send_realtime_event(request: Request):
    """
    Sends a realtime event (text, audio, or image) to an active session.
    Payloads follow the upstream event schema:
      { "session_id": str, "type": str, "data": str }
    """
    body = await request.json()
    try:
        return await forward_openai_request("v1/realtime/events", method="POST", json=body)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


# ----------------------------------------------------------
# GET /v1/realtime/events
# ----------------------------------------------------------
@router.get("/v1/realtime/events")
async def stream_realtime_events():
    """
    Streams realtime model output and session events using
    Server-Sent Events (SSE).
    """
    try:
        return await forward_openai_request("v1/realtime/events", method="GET")
    except Exception:
        # Return a graceful 501 response if upstream SSE is unavailable.
        return JSONResponse(
            content={"error": "realtime streaming unavailable"},
            status_code=501
        )
