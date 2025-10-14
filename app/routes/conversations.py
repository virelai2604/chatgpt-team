from fastapi import APIRouter, Request
from app.api.forward import forward_openai

router = APIRouter(prefix="/conversations")

@router.post("")
async def create_conversation(request: Request):
    """Create a new conversation."""
    return await forward_openai(request, "/v1/conversations")

@router.get("")
async def list_conversations(request: Request):
    """List all conversations."""
    return await forward_openai(request, "/v1/conversations")

@router.post("/{conversation_id}/messages")
async def send_message(request: Request, conversation_id: str):
    """Send a message to a conversation."""
    return await forward_openai(request, f"/v1/conversations/{conversation_id}/messages")

@router.get("/{conversation_id}/messages")
async def get_messages(request: Request, conversation_id: str):
    """List all messages in a conversation."""
    return await forward_openai(request, f"/v1/conversations/{conversation_id}/messages")

@router.get("/{conversation_id}")
async def get_conversation(request: Request, conversation_id: str):
    """Get conversation details."""
    return await forward_openai(request, f"/v1/conversations/{conversation_id}")
