# ================================================================
# realtime.py — Mock Realtime Session Routes
# ================================================================
# Implements a mock of OpenAI’s realtime endpoints:
#   POST /v1/realtime/sessions
#   POST /v1/realtime/events
#
# Test expectations:
#   - sessions return {"object": "realtime.session", "status": "queued"}
#   - events return {"object": "realtime.event", "status": "queued"}
# ================================================================

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
import time, uuid

router = APIRouter(prefix="/v1/realtime", tags=["realtime"])

@router.post("/sessions")
async def create_session(req: Request):
    """
    Create a realtime session.
    """
    data = await req.json()
    session_id = f"rs_{uuid.uuid4().hex[:8]}"
    return JSONResponse({
        "object": "realtime.session",
        "id": session_id,
        "model": data.get("model", "gpt-4o-realtime-preview"),
        "status": "queued",
        "created_at": int(time.time())
    })

@router.post("/events")
async def create_event(req: Request):
    """
    Mock event endpoint for realtime sessions.
    """
    event_data = await req.json()
    return JSONResponse({
        "object": "realtime.event",
        "id": f"evt_{uuid.uuid4().hex[:8]}",
        "type": event_data.get("type", "input_text"),
        "status": "queued"
    })
