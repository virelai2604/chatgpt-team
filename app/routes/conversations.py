# ==========================================================
# app/routes/conversations.py — BIFL v2.3.4-fp
# ==========================================================
# Unified conversation handler for multi-turn chat sessions.
# Supports streaming responses, DB logging, and cross-session continuity.
# ==========================================================

import json, datetime
from fastapi import APIRouter, Request
from app.api.forward import forward_openai
from app.utils.db_logger import log_event

router = APIRouter(prefix="/v1/conversations", tags=["Conversations"])

# ----------------------------------------------------------
# 💬 Create / Continue Conversation
# ----------------------------------------------------------
@router.post("")
async def create_conversation(request: Request):
    """
    Handles chat or reasoning conversations with streaming support.

    Example:
      {
        "model": "gpt-5-pro",
        "input": [
          {"role": "system", "content": "You are a helpful assistant."},
          {"role": "user", "content": "Tell me a joke."}
        ],
        "stream": true
      }
    """
    endpoint = "/v1/responses"
    response = await forward_openai(request, endpoint)

    try:
        await log_event("/v1/conversations", response.status_code, "conversation created")
    except Exception:
        pass

    return response


# ----------------------------------------------------------
# 📜 Retrieve Conversation Metadata
# ----------------------------------------------------------
@router.get("/{conv_id}")
async def get_conversation(request: Request, conv_id: str):
    """
    Retrieve metadata or logs for a specific conversation ID.
    This implementation delegates to upstream /v1/conversations/{id}.
    """
    endpoint = f"/v1/conversations/{conv_id}"
    return await forward_openai(request, endpoint)


# ----------------------------------------------------------
# 🧹 Delete Conversation
# ----------------------------------------------------------
@router.delete("/{conv_id}")
async def delete_conversation(request: Request, conv_id: str):
    """
    Delete a conversation record upstream or locally.
    """
    endpoint = f"/v1/conversations/{conv_id}"
    response = await forward_openai(request, endpoint)
    try:
        await log_event("/v1/conversations/delete", response.status_code, f"Deleted {conv_id}")
    except Exception:
        pass
    return response
