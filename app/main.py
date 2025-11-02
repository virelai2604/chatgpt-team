# ==============================================================
# main.py — ChatGPT Team Relay
# Ground Truth API v2.0 — SDK 2.6.1 Compatible
# ==============================================================

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse
import os, asyncio, json, time, uuid

# --------------------------------------------------------------
# Configuration
# --------------------------------------------------------------
RELAY_VERSION = "2.0"
SDK_TARGET = "openai-python 2.6.1"
DISABLE_PASSTHROUGH = os.getenv("DISABLE_PASSTHROUGH", "true").lower() == "true"

app = FastAPI(title="ChatGPT Team Relay", version=RELAY_VERSION)

# ==============================================================
# Health
# ==============================================================

@app.get("/health")
@app.get("/v1/health")
async def health():
    return JSONResponse({
        "object": "health",
        "status": "ok",
        "version": RELAY_VERSION,
        "sdk_target": SDK_TARGET,
        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "passthrough_enabled": not DISABLE_PASSTHROUGH
    })


# ==============================================================
# Models
# ==============================================================

@app.get("/models")
@app.get("/v1/models")
async def models():
    return JSONResponse({
        "object": "list",
        "data": [
            {"id": "gpt-5", "object": "model"},
            {"id": "gpt-4o", "object": "model"},
            {"id": "gpt-4o-mini", "object": "model"}
        ]
    })


# ==============================================================
# Embeddings
# ==============================================================

@app.post("/v1/embeddings")
async def embeddings(req: Request):
    body = await req.json()
    text = str(body.get("input", ""))
    embedding = [float(i) / 128 for i in range(128)]
    return JSONResponse({
        "object": "embedding",
        "data": [{"embedding": embedding, "index": 0}],
        "model": "mock-embedding",
        "usage": {"prompt_tokens": len(text), "total_tokens": len(text)}
    })


# ==============================================================
# Vector Stores CRUD
# ==============================================================

@app.post("/v1/vector_stores")
async def create_vector_store():
    vs_id = f"vs_{uuid.uuid4().hex[:8]}"
    return JSONResponse({
        "object": "vector_store",
        "id": vs_id,
        "created_at": int(time.time()),
        "metadata": {}
    })


@app.get("/v1/vector_stores/{vs_id}")
async def get_vector_store(vs_id: str):
    return JSONResponse({
        "object": "vector_store",
        "id": vs_id,
        "status": "ready",
        "created_at": int(time.time())
    })


@app.delete("/v1/vector_stores/{vs_id}")
async def delete_vector_store(vs_id: str):
    return JSONResponse({
        "object": "vector_store.deleted",
        "id": vs_id,
        "deleted": True
    })


# ==============================================================
# Files API
# ==============================================================

@app.post("/v1/files")
async def create_file():
    return JSONResponse({
        "object": "file",
        "id": f"file_{uuid.uuid4().hex[:8]}",
        "bytes": 128,
        "created": int(time.time()),
        "filename": "mock.txt",
        "purpose": "fine-tune"
    })


@app.get("/v1/files/{fid}")
async def get_file(fid: str):
    return JSONResponse({
        "object": "file",
        "id": fid,
        "bytes": 128,
        "created": int(time.time()),
        "filename": "mock.txt",
        "purpose": "test"
    })


@app.get("/v1/files/{fid}/content")
async def get_file_content(fid: str):
    return JSONResponse({
        "object": "file.content",
        "id": fid,
        "content": "mock data"
    })


# ==============================================================
# Realtime API  (expanded and ground-truth aligned)
# ==============================================================

REALTIME_SESSIONS = {}
REALTIME_EVENTS = {}

@app.post("/v1/realtime/sessions")
async def realtime_sessions(req: Request):
    """Create a realtime session aligned with OpenAI schema."""
    data = await req.json() if req.method == "POST" else {}
    session_id = f"rs_{uuid.uuid4().hex[:8]}"
    session = {
        "object": "realtime.session",
        "id": session_id,
        "model": data.get("model", "gpt-4o-realtime-preview"),
        "modalities": data.get("modalities", ["text", "image"]),
        "voice": data.get("voice", "none"),
        "status": "active",
        "created_at": int(time.time()),
        "expires_in": 3600
    }
    REALTIME_SESSIONS[session_id] = session
    REALTIME_EVENTS[session_id] = []
    return JSONResponse(session)


@app.post("/v1/realtime/events")
async def realtime_events(req: Request):
    """Create a realtime event associated with a session."""
    event_data = await req.json()
    session_id = event_data.get("session_id")
    event = {
        "object": "realtime.event",
        "id": f"evt_{uuid.uuid4().hex[:8]}",
        "session_id": session_id,
        "type": event_data.get("type", "input_text"),
        "status": "queued",
        "data": event_data.get("data", {}),
        "created_at": int(time.time())
    }
    if session_id in REALTIME_EVENTS:
        REALTIME_EVENTS[session_id].append(event)
    else:
        REALTIME_EVENTS[session_id] = [event]
    return JSONResponse(event)


@app.get("/v1/realtime/sessions/{session_id}/events")
async def list_realtime_events(session_id: str):
    """Retrieve all events for a given realtime session."""
    events = REALTIME_EVENTS.get(session_id, [])
    return JSONResponse({"object": "list", "data": events})


@app.get("/v1/realtime/sessions/{session_id}/stream")
async def stream_realtime_events(session_id: str):
    """Simulate realtime streaming via Server-Sent Events (SSE)."""
    async def stream():
        for e in REALTIME_EVENTS.get(session_id, []):
            await asyncio.sleep(0.1)
            yield f"data: {json.dumps(e)}\n\n"
        yield "data: [STREAM_COMPLETE]\n\n"
    return StreamingResponse(stream(), media_type="text/event-stream")


# ==============================================================
# Responses API  (core endpoint)
# ==============================================================

@app.post("/v1/responses")
async def responses(req: Request):
    body = await req.json()

    # Schema validation
    if not body.get("model") or not body.get("input"):
        return JSONResponse({
            "error": {
                "message": "Invalid request body: model and input required.",
                "type": "invalid_request_error",
                "code": "schema_violation"
            }
        }, status_code=400)

    # Background job simulation
    if body.get("background", False):
        return JSONResponse({
            "object": "response",
            "id": f"resp_{uuid.uuid4().hex[:8]}",
            "status": "queued"
        })

    # Streaming SSE
    if body.get("stream", False):
        resp_id = f"resp_{uuid.uuid4().hex[:8]}"

        async def event_gen():
            # created
            yield f'data: {json.dumps({\
                "type": "response.created",\
                "response": {\
                    "id": resp_id,\
                    "object": "response",\
                    "model": "gpt-5",\
                    "status": "in_progress",\
                    "output": [{\
                        "type": "message",\
                        "role": "assistant",\
                        "content": [{"type": "output_text", "text": ""}]\
                    }]\
                }\
            })}\n\n'
            yield f'data: {json.dumps({"type": "response.started", "id": resp_id, "object": "response"})}\n\n'
            yield f'data: {json.dumps({"type": "response.output_item.added","item":{"type":"message","role":"assistant","content":[]}})}\n\n'
            yield f'data: {json.dumps({"type": "response.content_part.added","output_index":0,"part":{"type":"output_text","text":""}})}\n\n'
            for chunk in ["Hello from stream ", "chunk 1 ", "chunk 2"]:
                await asyncio.sleep(0.05)
                yield f'data: {json.dumps({"type":"response.output_text.delta","output_index":0,"content_index":0,"delta":chunk})}\n\n'
                yield f'data: {json.dumps({"type":"message.delta","delta":{"role":"assistant","content":[{"type":"output_text","text":chunk}]}})}\n\n'
            yield f'data: {json.dumps({\
                "type": "response.completed",\
                "response": {\
                    "id": resp_id,\
                    "object": "response",\
                    "model": "gpt-5",\
                    "status": "completed",\
                    "output": [{\
                        "type": "message",\
                        "role": "assistant",\
                        "content": [{"type": "output_text","text": "stream complete"}]\
                    }]\
                }\
            })}\n\n'
        return StreamingResponse(event_gen(), media_type="text/event-stream")

    # Non-stream synchronous response
    tool_name = None
    if body.get("tools"):
        t = body["tools"][0]
        tool_name = t.get("type")

    output_text = f"Executed tool {tool_name or 'none'} successfully."

    return JSONResponse({
        "object": "response",
        "id": f"resp_{uuid.uuid4().hex[:8]}",
        "model": body["model"],
        "output": [{
            "type": "message",
            "role": "assistant",
            "content": [{"type": "output_text", "text": output_text}]
        }],
        "tool_outputs": [{
            "tool": tool_name or "mock_tool",
            "status": "success",
            "output": {"result": "ok"}
        }],
        "usage": {"total_tokens": 5},
        "status": "completed"
    })


# ==============================================================
# Response Aliases
# ==============================================================

@app.post("/responses")
async def responses_root(req: Request):
    return await responses(req)

@app.post("/v1/responses:stream")
async def responses_stream(req: Request):
    return await responses(req)

@app.post("/responses:stream")
async def responses_stream_root(req: Request):
    return await responses(req)


# ==============================================================
# Fallback passthrough proxy
# ==============================================================

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def fallback(path: str):
    return JSONResponse({
        "object": "fallback",
        "path": path,
        "status": "ok",
        "passthrough": not DISABLE_PASSTHROUGH
    })
