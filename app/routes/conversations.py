# ================================================================
# conversations.py — Local mock persistence API
# ================================================================
# Simulates OpenAI's historical /v1/conversations endpoints.
# Stores and retrieves minimal conversation metadata.
# ================================================================

import time
import uuid
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/v1/conversations", tags=["conversations"])

# In-memory conversation store (can be replaced with SQLite)
CONVERSATIONS = {}

@router.get("")
async def list_conversations():
    """Lists all stored conversations."""
    data = list(CONVERSATIONS.values())
    return JSONResponse({
        "object": "list",
        "data": data
    })

@router.post("")
async def create_conversation(request: Request):
    """Creates a new conversation record."""
    body = await request.json() if request.headers.get("content-type") == "application/json" else {}
    conv_id = f"conv_{uuid.uuid4().hex[:8]}"
    conversation = {
        "object": "conversation",
        "id": conv_id,
        "title": body.get("title", "Untitled conversation"),
        "created": int(time.time()),
        "messages": body.get("messages", []),
    }
    CONVERSATIONS[conv_id] = conversation
    return JSONResponse(conversation)

@router.get("/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Retrieves a conversation by ID."""
    if conversation_id not in CONVERSATIONS:
        return JSONResponse({"error": "Conversation not found"}, status_code=404)
    return JSONResponse(CONVERSATIONS[conversation_id])

@router.delete("/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Deletes a conversation by ID."""
    if conversation_id in CONVERSATIONS:
        del CONVERSATIONS[conversation_id]
        return JSONResponse({"object": "conversation.deleted", "id": conversation_id, "deleted": True})
    return JSONResponse({"error": "Conversation not found"}, status_code=404)
