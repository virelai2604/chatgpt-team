from __future__ import annotations

import logging

from fastapi import APIRouter, Request, Response

from app.api.forward_openai import forward_openai_request

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/v1",
    tags=["conversations"],
)


@router.post("/conversations")
async def create_conversation(request: Request) -> Response:
    """
    POST /v1/conversations

    Create a conversation.
    Mirrors:
    https://platform.openai.com/docs/api-reference/conversations/create
    """
    logger.debug("Proxying POST /v1/conversations to OpenAI")
    return await forward_openai_request(request)


@router.get("/conversations/{conversation_id}")
async def retrieve_conversation(conversation_id: str, request: Request) -> Response:
    """
    GET /v1/conversations/{conversation_id}

    Retrieve a conversation.
    Mirrors:
    https://platform.openai.com/docs/api-reference/conversations/retrieve
    """
    logger.debug("Proxying GET /v1/conversations/%s to OpenAI", conversation_id)
    return await forward_openai_request(request)


@router.post("/conversations/{conversation_id}")
async def update_conversation(conversation_id: str, request: Request) -> Response:
    """
    POST /v1/conversations/{conversation_id}

    Update a conversation (metadata).
    Mirrors:
    https://platform.openai.com/docs/api-reference/conversations/update
    """
    logger.debug("Proxying POST /v1/conversations/%s to OpenAI", conversation_id)
    return await forward_openai_request(request)


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str, request: Request) -> Response:
    """
    DELETE /v1/conversations/{conversation_id}

    Delete a conversation.
    Mirrors:
    https://platform.openai.com/docs/api-reference/conversations/delete
    """
    logger.debug("Proxying DELETE /v1/conversations/%s to OpenAI", conversation_id)
    return await forward_openai_request(request)


@router.get("/conversations/{conversation_id}/items")
async def list_conversation_items(conversation_id: str, request: Request) -> Response:
    """
    GET /v1/conversations/{conversation_id}/items

    List all items in a conversation.
    Mirrors:
    https://platform.openai.com/docs/api-reference/conversations/list-items
    """
    logger.debug(
        "Proxying GET /v1/conversations/%s/items to OpenAI", conversation_id
    )
    return await forward_openai_request(request)


@router.post("/conversations/{conversation_id}/items")
async def create_conversation_items(
    conversation_id: str,
    request: Request,
) -> Response:
    """
    POST /v1/conversations/{conversation_id}/items

    Create items in a conversation.
    Mirrors:
    https://platform.openai.com/docs/api-reference/conversations/create-item
    """
    logger.debug(
        "Proxying POST /v1/conversations/%s/items to OpenAI", conversation_id
    )
    return await forward_openai_request(request)


@router.get("/conversations/{conversation_id}/items/{item_id}")
async def retrieve_conversation_item(
    conversation_id: str,
    item_id: str,
    request: Request,
) -> Response:
    """
    GET /v1/conversations/{conversation_id}/items/{item_id}

    Retrieve a single item.
    Mirrors:
    https://platform.openai.com/docs/api-reference/conversations/retrieve-item
    """
    logger.debug(
        "Proxying GET /v1/conversations/%s/items/%s to OpenAI",
        conversation_id,
        item_id,
    )
    return await forward_openai_request(request)


@router.delete("/conversations/{conversation_id}/items/{item_id}")
async def delete_conversation_item(
    conversation_id: str,
    item_id: str,
    request: Request,
) -> Response:
    """
    DELETE /v1/conversations/{conversation_id}/items/{item_id}

    Delete a conversation item.
    Mirrors:
    https://platform.openai.com/docs/api-reference/conversations/delete-item
    """
    logger.debug(
        "Proxying DELETE /v1/conversations/%s/items/%s to OpenAI",
        conversation_id,
        item_id,
    )
    return await forward_openai_request(request)
