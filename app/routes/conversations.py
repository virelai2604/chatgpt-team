# ==========================================================
# app/api/conversations.py — Ground Truth Conversations API
# ==========================================================
"""
Implements /v1/conversations — a lightweight context management layer.

Each conversation acts as a container for messages, metadata, and state
shared across multiple /v1/responses calls.

This module mirrors the OpenAI API behavior (2025.10 spec):
  - Stateless by default (in-memory)
  - Simple CRUD routes for listing, creating, fetching, and deleting
  - Optional "metadata" and "messages" fields
  - No external database required
"""

import uuid
import time
import logging
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger("conversations")
router = APIRouter(prefix="/v1/conversations", tags=["Conversations"])

# ----------------------------------------------------------
# In-memory store for conversation state
# ----------------------------------------------------------
_CONVERSATIONS: dict[str, dict] = {}


# ----------------------------------------------------------
# Helper: create a new conversation object
# ----------------------------------------------------------
def _new_conversation(title: str | None = None, metadata: dict | None = None):
    convo_id = f"cnv_{uuid.uuid4().hex[:24]}"
    now = int(time.time())
    conversation = {
        "id": convo_id,
        "object": "conversation",
        "title": title or f"Conversation {convo_id[-4:]}",
        "created_at": now,
        "updated_at": now,
        "metadata": metadata or {},
        "messages": [],
    }
    _CONVERSATIONS[convo_id] = conversation
    logger.info(f"🗨️ Created conversation {convo_id}")
    return conversation


# ----------------------------------------------------------
# Routes
# ----------------------------------------------------------

@router.get("")
async def list_conversations():
    """List all active conversations."""
    return {"object": "list", "data": list(_CONVERSATIONS.values())}


@router.post("")
async def create_conversation(request: Request):
    """Create a new conversation."""
    try:
        payload = await request.json()
    except Exception:
        payload = {}

    title = payload.get("title")
    metadata = payload.get("metadata", {})
    convo = _new_conversation(title, metadata)
    return JSONResponse(convo, status_code=201)


@router.get("/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Retrieve a single conversation by ID."""
    convo = _CONVERSATIONS.get(conversation_id)
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return convo


@router.delete("/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete a conversation."""
    if conversation_id not in _CONVERSATIONS:
        raise HTTPException(status_code=404, detail="Conversation not found")
    del _CONVERSATIONS[conversation_id]
    logger.info(f"🗑️ Deleted conversation {conversation_id}")
    return {"deleted": True, "id": conversation_id}


@router.post("/{conversation_id}/messages")
async def append_message(conversation_id: str, request: Request):
    """
    Append a message to a conversation.
    Typically used internally by /v1/responses to maintain state.
    """
    convo = _CONVERSATIONS.get(conversation_id)
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")

    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    message = {
        "id": f"msg_{uuid.uuid4().hex[:24]}",
        "role": payload.get("role", "user"),
        "content": payload.get("content"),
        "timestamp": int(time.time()),
    }

    convo["messages"].append(message)
    convo["updated_at"] = int(time.time())
    logger.debug(f"💬 Added message to {conversation_id}")
    return message


@router.get("/{conversation_id}/messages")
async def list_messages(conversation_id: str):
    """List messages within a conversation."""
    convo = _CONVERSATIONS.get(conversation_id)
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"object": "list", "data": convo["messages"]}
