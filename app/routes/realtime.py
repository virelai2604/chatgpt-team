# ================================================================
# realtime.py — Expanded Mock Realtime Session Routes
# ================================================================
# Implements a complete mock of OpenAI’s realtime endpoints:
#   POST /v1/realtime/sessions
#   POST /v1/realtime/events
#   GET  /v1/realtime/sessions/{session_id}/events
#
# Conforms to OpenAI SDK v2.6.1 / Node v6.7.0 structure:
#   - realtime.session object
#   - realtime.event object
#
# Ground-truth alignment:
#   Matches ChatGPT-API_reference_ground_truth-2025-10-29.json schema
# ================================================================

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse
import time, uuid, asyncio

router = APIRouter(prefix="/v1/realtime", tags=["realtime"])

# ----------------------------------------------------------------
# In-memory stores for mock sessions and events
# ----------------------------------------------------------------
REALTIME_SESSIONS = {}
REALTIME_EVENTS = {}

# ----------------------------------------------------------------
# POST /v1/realtime/sessions
# ----------------------------------------------------------------
@router.post("/sessions")
async def create_session(req: Request):
    """
    Create a realtime session.
    Ground-truth fields:
        - object: "realtime.session"
        - id: rs_xxx
        - model: e.g. gpt-4o-realtime-preview
        - modalities: ["text", "image"]
        - voice: optional voice identifier
        - status: "active" | "queued"
        - created_at: UNIX timestamp
        - expires_in: session lifetime (s)
    """
    data = await req.json()
    session_id = f"rs_{uuid.uuid4().hex[:8]}"

    session = {
        "object": "realtime.session",
        "id": session_id,
        "model": data.get("model", "gpt-4o-realtime-preview"),
        "modalities": data.get("modalities", ["text", "image"]),
        "voice": data.get("voice", "none"),
        "status": "active",
        "created_at": int(time.time()),
        "expires_in": 3600,
    }

    REALTIME_SESSIONS[session_id] = session
    REALTIME_EVENTS[session_id] = []
    return JSONResponse(session)

# ----------------------------------------------------------------
# POST /v1/realtime/events
# ----------------------------------------------------------------
@router.post("/events")
async def create_event(req: Request):
    """
    Create a realtime event associated with a session.
    Ground-truth fields:
        - object: "realtime.event"
        - id: evt_xxx
        - session_id: link to parent session
        - type: input_text | input_image | input_tool | input_file
        - status: "queued"
        - data: payload dictionary
        - created_at: UNIX timestamp
    """
    event_data = await req.json()
    session_id = event_data.get("session_id")

    event = {
        "object": "realtime.event",
        "id": f"evt_{uuid.uuid4().hex[:8]}",
        "session_id": session_id,
        "type": event_data.get("type", "input_text"),
        "status": "queued",
        "data": event_data.get("data", {}),
        "created_at": int(time.time()),
    }

    if session_id in REALTIME_EVENTS:
        REALTIME_EVENTS[session_id].append(event)
    else:
        REALTIME_EVENTS[session_id] = [event]

    return JSONResponse(event)

# ----------------------------------------------------------------
# GET /v1/realtime/sessions/{session_id}/events
# ----------------------------------------------------------------
@router.get("/sessions/{session_id}/events")
async def list_events(session_id: str):
    """
    Retrieve all events for a given realtime session.
    Returns:
        {
            "object": "list",
            "data": [ ...realtime.event objects... ]
        }
    """
    events = REALTIME_EVENTS.get(session_id, [])
    return JSONResponse({
        "object": "list",
        "data": events
    })

# ----------------------------------------------------------------
# GET /v1/realtime/sessions/{session_id}/stream
# ----------------------------------------------------------------
@router.get("/sessions/{session_id}/stream")
async def stream_events(session_id: str):
    """
    Stream queued events for a given session using Server-Sent Events (SSE).
    Simulates Realtime API streaming (WebSocket equivalent).
    """

    async def event_stream():
        for event in REALTIME_EVENTS.get(session_id, []):
            await asyncio.sleep(0.1)
            yield f"data: {event}\n\n"
        yield "data: [STREAM_COMPLETE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
