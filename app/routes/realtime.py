# ==========================================================
# app/routes/realtime.py — Relay v2025-10 Ground-Truth Mirror
# ==========================================================
# Implements /v1/realtime/* routes to match OpenAI’s Realtime API.
# Supports creation, event streaming, and termination of sessions.
# Used by GPT-4o-Realtime, GPT-5-Pro-Realtime, and multimodal models.
# ==========================================================

from fastapi import APIRouter, Request
from app.api.forward_openai import forward_openai
import logging

router = APIRouter(prefix="/v1/realtime", tags=["Realtime"])

# ----------------------------------------------------------
# 🎧 POST /v1/realtime/sessions — Create Realtime Session
# ----------------------------------------------------------
@router.post("/sessions")
async def create_session(request: Request):
    """
    Mirrors POST /v1/realtime/sessions.
    Creates a new realtime session (text, audio, or video).
    """
    endpoint = "realtime/sessions"
    response = await forward_openai(request, endpoint)
    try:
        await log_event("info", f"create realtime session {response.status_code}")
    except Exception as e:
        logging.warning(f"[Realtime] Failed to log session creation: {e}")
    return response

# ----------------------------------------------------------
# 🔄 POST /v1/realtime/events — Send Events to Session
# ----------------------------------------------------------
@router.post("/events")
async def send_event(request: Request):
    """
    Mirrors POST /v1/realtime/events.
    Sends user or system events (messages, audio frames, control signals)
    into an active realtime session.
    """
    endpoint = "realtime/events"
    response = await forward_openai(request, endpoint)
    try:
        await log_event("info", f"post realtime event {response.status_code}")
    except Exception as e:
        logging.warning(f"[Realtime] Failed to log realtime event: {e}")
    return response

# ----------------------------------------------------------
# ❌ DELETE /v1/realtime/sessions/{session_id} — Terminate
# ----------------------------------------------------------
@router.delete("/sessions/{session_id}")
async def delete_session(request: Request, session_id: str):
    """
    Mirrors DELETE /v1/realtime/sessions/{session_id}.
    Terminates a running realtime session gracefully.
    """
    endpoint = f"realtime/sessions/{session_id}"
    response = await forward_openai(request, endpoint)
    try:
        await log_event("info", f"delete realtime session {session_id} {response.status_code}")
    except Exception as e:
        logging.warning(f"[Realtime] Failed to log session termination: {e}")
    return response

# Dummy async logger (optional)
async def log_event(level: str, message: str):
    logging.log(getattr(logging, level.upper(), logging.INFO), f"[Realtime] {message}")
