from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import Response

from app.api.forward_openai import forward_openai_request

router = APIRouter(prefix="/v1", tags=["chat"])


@router.post("/chat/completions")
async def create_chat_completion(request: Request) -> Response:
    """
    POST /v1/chat/completions

    Transparent passthrough to upstream OpenAI, matching the OpenAI Python SDK's
    ``client.chat.completions.create()``. Supports streaming when the caller
    sends ``Accept: text/event-stream`` or a body with ``{"stream": true}``.
    """
    return await forward_openai_request(request, upstream_path="/v1/chat/completions")
