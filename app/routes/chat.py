# ==========================================================
# app/routes/chat.py — Relay v2025-10 Ground Truth Mirror
# ==========================================================
# OpenAI-compatible /v1/chat/completions endpoint.
# Core inference route for GPT-4, GPT-5, Codex, and O-Series models.
# Supports streaming, multimodal content, and DB-logged events.
# ==========================================================

from fastapi import APIRouter, Request
from app.api.forward_openai import forward_openai
from app.utils.db_logger import log_event

router = APIRouter(prefix="/v1", tags=["Chat"])

# ----------------------------------------------------------
# 💬  Chat Completions
# ----------------------------------------------------------
@router.post("/chat/completions")
async def chat_completions(request: Request):
    """
    Core model inference endpoint.

    Mirrors POST /v1/chat/completions from the OpenAI API.
    Handles all GPT-family models (GPT-4, GPT-5, Codex, O-Series),
    and supports streaming responses, tools, and multimodal content.

    Example:
        POST /v1/chat/completions
        {
            "model": "gpt-5",
            "messages": [
                {"role": "user", "content": "Write a haiku about memory."}
            ],
            "stream": true
        }
    """
    endpoint = "/v1/chat/completions"
    response = await forward_openai(request, endpoint)

    try:
        await log_event(endpoint, response.status_code, "chat completion request")
    except Exception:
        pass

    return response
