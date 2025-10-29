# ==========================================================
# app/routes/chat.py — Ground Truth OpenAI-Compatible Mirror
# ==========================================================
from fastapi import APIRouter, Request
from app.api.forward_openai import forward_openai_request

router = APIRouter(prefix="/v1/chat", tags=["Chat"])

@router.post("/completions")
async def chat_completions(request: Request):
    """
    Mirrors OpenAI POST /v1/chat/completions
    Core endpoint for GPT-family models with streaming and tool calls.
    """
    body = await request.json()
    stream = bool(body.get("stream", False))
    result = await forward_openai_request("v1/chat/completions", method="POST", json_data=body, stream=stream)
    if stream:
        from fastapi.responses import StreamingResponse
        return StreamingResponse(result, media_type="text/event-stream")
    from fastapi.responses import JSONResponse
    return JSONResponse(result)
