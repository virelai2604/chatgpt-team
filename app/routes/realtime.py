# ================================================================
# realtime.py — Realtime session & event passthrough
# ================================================================
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from app.api.forward_openai import forward_to_openai

router = APIRouter(prefix="/v1/realtime", tags=["realtime"])

@router.post("/sessions")
async def create_session(request: Request):
    resp = await forward_to_openai(request, "/v1/realtime/sessions")
    return JSONResponse(resp.json(), status_code=resp.status_code)

@router.post("/events")
async def create_event(request: Request):
    resp = await forward_to_openai(request, "/v1/realtime/events")
    return JSONResponse(resp.json(), status_code=resp.status_code)

@router.get("/sessions/{session_id}/events")
async def list_events(session_id: str, request: Request):
    resp = await forward_to_openai(request, f"/v1/realtime/sessions/{session_id}/events")
    return JSONResponse(resp.json(), status_code=resp.status_code)

@router.get("/sessions/{session_id}/stream")
async def stream_events(session_id: str, request: Request):
    resp = await forward_to_openai(request, f"/v1/realtime/sessions/{session_id}/stream")
    return JSONResponse(resp.json(), status_code=resp.status_code)
