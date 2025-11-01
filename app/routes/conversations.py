"""
conversations.py — /v1/conversations
Implements conversation and thread memory management.
Ground Truth API v1.7 + OpenAI SDK 2.6.1 compliant.
"""

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, Any
import time
import uuid
from app.utils.logger import logger

router = APIRouter()

# In-memory store for demo (replace with DB later)
CONVERSATIONS: Dict[str, Dict[str, Any]] = {}

@router.post("/v1/conversations")
async def create_conversation(request: Request):
    body = await request.json()
    conv_id = f"conv_{uuid.uuid4().hex[:10]}"
    CONVERSATIONS[conv_id] = {
        "id": conv_id,
        "object": "conversation",
        "created": int(time.time()),
        "metadata": body.get("metadata", {}),
        "items": []
    }
    logger.info(f"Created conversation {conv_id}")
    return JSONResponse(CONVERSATIONS[conv_id])

@router.get("/v1/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    conv = CONVERSATIONS.get(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv

@router.post("/v1/conversations/{conversation_id}")
async def update_conversation(conversation_id: str, request: Request):
    body = await request.json()
    conv = CONVERSATIONS.get(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    conv["metadata"].update(body.get("metadata", {}))
    return conv

@router.delete("/v1/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    if conversation_id in CONVERSATIONS:
        del CONVERSATIONS[conversation_id]
    return {"id": conversation_id, "object": "conversation", "deleted": True}

@router.get("/v1/conversations/{conversation_id}/items")
async def list_conversation_items(conversation_id: str):
    conv = CONVERSATIONS.get(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"object": "list", "data": conv["items"]}

@router.post("/v1/conversations/{conversation_id}/items")
async def add_conversation_item(conversation_id: str, request: Request):
    conv = CONVERSATIONS.get(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    body = await request.json()
    item = {
        "id": f"item_{uuid.uuid4().hex[:8]}",
        "object": "conversation.item",
        "created": int(time.time()),
        "role": body.get("role", "user"),
        "content": body.get("content", "")
    }
    conv["items"].append(item)
    return item
