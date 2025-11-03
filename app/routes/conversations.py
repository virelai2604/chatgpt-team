# ================================================================
# conversations.py — /v1/conversations API Route
# ================================================================
# Provides RESTful access to stored conversations.
# Wraps around data/conversations for persistence and management.
# ================================================================

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from app.utils.logger import logger
import data.conversations as conversations  # ✅ Correct import (not app.data)

router = APIRouter(prefix="/v1/conversations", tags=["conversations"])


@router.get("/")
async def list_all_conversations():
    """
    Lists all stored conversation IDs.
    Returns: JSON list of conversation identifiers.
    """
    try:
        ids = conversations.list_conversations()
        logger.info(f"🗂️ Listed {len(ids)} conversations.")
        return {"object": "list", "data": ids, "has_more": False}
    except Exception as e:
        logger.error(f"❌ Failed to list conversations: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.get("/{conversation_id}")
async def get_conversation(conversation_id: str):
    """
    Retrieves a specific conversation by ID.
    Returns: Full conversation JSON (id, messages, metadata).
    """
    try:
        data_obj = conversations.get_conversation(conversation_id)
        logger.info(f"📖 Retrieved conversation {conversation_id}")
        return data_obj
    except Exception as e:
        logger.error(f"❌ Failed to load conversation {conversation_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.post("/{conversation_id}/messages")
async def add_message(conversation_id: str, request: Request):
    """
    Appends a new message to the conversation log.
    Expected body: {"role": "user|assistant|system", "content": "string"}
    """
    try:
        payload = await request.json()
        role = payload.get("role")
        content = payload.get("content")

        if not role or not content:
            raise HTTPException(status_code=400, detail="Missing 'role' or 'content'")

        conversations.save_message(conversation_id, role, content)
        logger.info(f"💬 Added {role} message to conversation {conversation_id}")

        return JSONResponse(
            status_code=200,
            content={
                "id": conversation_id,
                "object": "message",
                "status": "saved",
                "role": role,
                "content": content,
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to save message: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.delete("/{conversation_id}")
async def remove_conversation(conversation_id: str):
    """
    Deletes a stored conversation file.
    Returns success indicator.
    """
    try:
        result = conversations.delete_conversation(conversation_id)
        if result:
            return {"id": conversation_id, "deleted": True}
        raise HTTPException(status_code=404, detail="Conversation not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to delete conversation: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
