# ==========================================================
# app/routes/conversations.py — Ground Truth OpenAI-Compatible Mirror
# ==========================================================
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from app.api.forward_openai import forward_openai_request

router = APIRouter(prefix="/v1/conversations", tags=["Conversations"])

@router.post("")
async def create_conversation(request: Request):
    """
    Mirrors OpenAI POST /v1/conversations
    Creates a new conversation object.
    """
    body = await request.json()
    result = await forward_openai_request("v1/conversations", method="POST", json_data=body)
    return JSONResponse(result)

@router.get("/{conversation_id}")
async def get_conversation(conversation_id: str):
    """
    Mirrors OpenAI GET /v1/conversations/{conversation_id}
    Retrieves a conversation by ID.
    """
    result = await forward_openai_request(f"v1/conversations/{conversation_id}", method="GET")
    return JSONResponse(result)

@router.post("/{conversation_id}")
async def update_conversation(conversation_id: str, request: Request):
    """
    Mirrors OpenAI POST /v1/conversations/{conversation_id}
    Updates metadata or state for a conversation.
    """
    body = await request.json()
    endpoint = f"v1/conversations/{conversation_id}"
    result = await forward_openai_request(endpoint, method="POST", json_data=body)
    return JSONResponse(result)

@router.delete("/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """
    Mirrors OpenAI DELETE /v1/conversations/{conversation_id}
    Deletes the specified conversation.
    """
    endpoint = f"v1/conversations/{conversation_id}"
    result = await forward_openai_request(endpoint, method="DELETE")
    return JSONResponse(result)
