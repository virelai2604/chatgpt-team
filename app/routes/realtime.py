# ==========================================================
# app/routes/realtime.py — Relay v2025-10 Ground Truth Mirror
# ==========================================================
# OpenAI-compatible /v1/realtime endpoint.
# Supports creation, interaction, and termination of realtime sessions.
# Used by GPT-4o-Realtime, GPT-5-Pro-Realtime, and audio/video chat sessions.
# ==========================================================

from fastapi import APIRouter, Request
from app.api.forward_openai import forward_openai
from app.utils.db_logger import log_event, logging

router = APIRouter(prefix="/v1/realtime", tags=["Realtime"])

# ----------------------------------------------------------
# 🎧 Create Realtime Session
# ----------------------------------------------------------
@router.post("/sessions")
async def create_session(request: Request):
    """
    Mirrors POST /v1/realtime/sessions
    Creates a new realtime session (text, audio, or video).
    """
    endpoint = "/v1/realtime/sessions"
    response = await forward_openai(request, endpoint)
    try:
        await log_event("info", f"create realtime session {response.status_code}")
    except Exception as e:
        logging.warning(f"Failed to log realtime session creation: {e}")
    return response

# ----------------------------------------------------------
# 🔄 Send Events into Active Session
# ----------------------------------------------------------
@router.post("/events")
async def send_event(request: Request):
    """
    Mirrors POST /v1/realtime/events
    Sends user or system events (messages, audio frames, controls)
    into an active realtime session.
    """
    endpoint = "/v1/realtime/events"
    response = await forward_openai(request, endpoint)
    try:
        await log_event("info", f"post realtime event {response.status_code}")
    except Exception as e:
        logging.warning(f"Failed to log realtime event: {e}")
    return response

# ----------------------------------------------------------
# ❌ Terminate Realtime Session
# ----------------------------------------------------------
@router.delete("/sessions/{session_id}")
async def delete_session(request: Request, session_id: str):
    """
    Mirrors DELETE /v1/realtime/sessions/{session_id}
    Terminates a running realtime session.
    """
    endpoint = f"/v1/realtime/sessions/{session_id}"
    response = await forward_openai(request, endpoint)
    try:
        await log_event("info", f"delete realtime session {session_id} {response.status_code}")
    except Exception as e:
        logging.warning(f"Failed to log realtime deletion: {e}")
    return response
