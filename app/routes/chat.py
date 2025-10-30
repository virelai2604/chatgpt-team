from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse, JSONResponse
import httpx
import os

router = APIRouter(prefix="/v1/chat", tags=["Chat"])

OPENAI_BASE = os.getenv("OPENAI_BASE_URL", "https://api.openai.com")
API_KEY = os.getenv("OPENAI_API_KEY")
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}


@router.post("/completions")
async def chat_completions(request: Request):
    """POST /v1/chat/completions — supports both stream and non-stream."""
    payload = await request.json()
    stream = bool(payload.get("stream", False))

    if not stream:
        async with httpx.AsyncClient(timeout=None) as client:
            r = await client.post(f"{OPENAI_BASE}/v1/chat/completions", headers=HEADERS, json=payload)
        return JSONResponse(r.json(), status_code=r.status_code)

    async def stream_response():
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream("POST", f"{OPENAI_BASE}/v1/chat/completions", headers=HEADERS, json=payload) as r:
                async for chunk in r.aiter_bytes():
                    yield chunk

    return StreamingResponse(stream_response(), media_type="text/event-stream")
