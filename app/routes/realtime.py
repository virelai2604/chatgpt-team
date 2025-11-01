"""
realtime.py — /v1/realtime
Ground Truth API v1.7 + OpenAI SDK 2.6.1 alignment

Implements:
  • POST /v1/realtime/sessions
  • GET  /v1/realtime/models
  • GET  /v1/realtime/stream
  • POST /v1/realtime/events

Handles realtime model sessions, streaming, and event injection.
"""

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
import uuid
import time
import asyncio
from app.utils.logger import logger

router = APIRouter()

# In-memory realtime session store
REALTIME_SESSIONS = {}

# --------------------------------------------------------------------------
# 1. Create a realtime session
# --------------------------------------------------------------------------

@router.post("/v1/realtime/sessions")
async def create_realtime_session(request: Request):
    """
    Create a new realtime session for a model.
    SDK equivalent: client.realtime.sessions.create()
    """
    try:
        body = await request.json()
    except Exception:
        body = {}

    model = body.get("model", "gpt-4o-realtime-preview")
    modalities = body.get("modalities", ["text"])
    voice = body.get("voice", "verse")

    session_id = f"rt_{uuid.uuid4().hex[:10]}"
    session = {
        "id": session_id,
        "object": "realtime.session",
        "created": int(time.time()),
        "model": model,
        "modalities": modalities,
        "voice": voice,
        "status": "active",
        "events": []
    }

    REALTIME_SESSIONS[session_id] = session
    logger.info(f"Realtime session created: {session_id} for model {model}")
    return JSONResponse(session)


# --------------------------------------------------------------------------
# 2. List realtime-capable models
# --------------------------------------------------------------------------

@router.get("/v1/realtime/models")
async def list_realtime_models():
    """
    List available realtime models.
    SDK equivalent: client.realtime.models.list()
    """
    models = [
        {
            "id": "gpt-4o-realtime-preview",
            "object": "model",
            "type": "realtime",
            "created": int(time.time()),
            "owned_by": "openai"
        },
        {
            "id": "gpt-5-realtime-alpha",
            "object": "model",
            "type": "realtime",
            "created": int(time.time()),
            "owned_by": "openai"
        }
    ]
    return {"object": "list", "data": models}


# --------------------------------------------------------------------------
# 3. Stream realtime output (SSE simulation)
# --------------------------------------------------------------------------

@router.get("/v1/realtime/stream")
async def stream_realtime(request: Request):
    """
    Open a live SSE stream for realtime output.
    SDK equivalent: client.realtime.stream()
    """
    async def event_stream():
        logger.info("Realtime stream opened.")
        for i in range(5):
            chunk = {
                "event": "realtime.output",
                "timestamp": int(time.time()),
                "data": f"Realtime output chunk {i + 1}"
            }
            yield f"data: {chunk}\n\n"
            await asyncio.sleep(0.5)
        yield "data: {\"event\": \"done\"}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# --------------------------------------------------------------------------
# 4. Post live input events
# --------------------------------------------------------------------------

@router.post("/v1/realtime/events")
async def post_realtime_event(request: Request):
    """
    Inject live events into an active realtime session.
    SDK equivalent: client.realtime.events.create()

    Typical event types:
      - input_text: { "text": "Hello world" }
      - input_audio: base64 audio chunk
      - input_image: base64 image or reference
      - metadata: { ... }
      - stop: {}

    These events are queued to the session’s internal state.
    """
    body = await request.json()
    session_id = body.get("session_id")
    event_type = body.get("type")
    data = body.get("data", {})

    if not session_id:
        raise HTTPException(status_code=400, detail="Missing session_id")
    if session_id not in REALTIME_SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found")

    session = REALTIME_SESSIONS[session_id]
    if session.get("status") != "active":
        raise HTTPException(status_code=400, detail="Session is not active")

    event_id = f"evt_{uuid.uuid4().hex[:8]}"
    event = {
        "id": event_id,
        "object": "realtime.event",
        "session_id": session_id,
        "type": event_type,
        "data": data,
        "created": int(time.time()),
        "status": "queued"
    }

    session["events"].append(event)
    logger.info(f"Realtime event added to {session_id}: {event_type}")
    return JSONResponse(event)
