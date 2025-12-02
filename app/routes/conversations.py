# app/routes/conversations.py

from __future__ import annotations

from fastapi import APIRouter, Request, Response

from app.api.forward_openai import forward_openai_request

router = APIRouter(
    prefix="/v1",
    tags=["conversations"],
)


@router.post("/conversations")
async def create_conversation(request: Request) -> Response:
    """
    POST /v1/conversations

    Create a new conversation object in OpenAI.
    """
    return await forward_openai_request(request)


@router.get("/conversations/{conversation_id}")
async def retrieve_conversation(conversation_id: str, request: Request) -> Response:
    """
    GET /v1/conversations/{conversation_id}

    Retrieve a single conversation by ID.
    """
    return await forward_openai_request(request)


@router.post("/conversations/{conversation_id}")
async def update_conversation(conversation_id: str, request: Request) -> Response:
    """
    POST /v1/conversations/{conversation_id}

    Update conversation metadata. Mirrors the official Conversations API.
    """
    return await forward_openai_request(request)


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str, request: Request) -> Response:
    """
    DELETE /v1/conversations/{conversation_id}

    Delete a conversation. Items are not deleted, per OpenAI API semantics.
    """
    return await forward_openai_request(request)


@router.get("/conversations/{conversation_id}/items")
async def list_conversation_items(
    conversation_id: str,
    request: Request,
) -> Response:
    """
    GET /v1/conversations/{conversation_id}/items

    List all items in the given conversation.
    Supports standard query params like `limit`, `after`, `order`, `include`.
    """
    return await forward_openai_request(request)


@router.post("/conversations/{conversation_id}/items")
async def create_conversation_items(
    conversation_id: str,
    request: Request,
) -> Response:
    """
    POST /v1/conversations/{conversation_id}/items

    Create one or more items in the given conversation.
    """
    return await forward_openai_request(request)


@router.get("/conversations/{conversation_id}/items/{item_id}")
async def retrieve_conversation_item(
    conversation_id: str,
    item_id: str,
    request: Request,
) -> Response:
    """
    GET /v1/conversations/{conversation_id}/items/{item_id}

    Retrieve a single item from a conversation.
    """
    return await forward_openai_request(request)


@router.delete("/conversations/{conversation_id}/items/{item_id}")
async def delete_conversation_item(
    conversation_id: str,
    item_id: str,
    request: Request,
) -> Response:
    """
    DELETE /v1/conversations/{conversation_id}/items/{item_id}

    Delete a single item from a conversation.
    """
    return await forward_openai_request(request)
