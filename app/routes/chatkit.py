# app/routes/chatkit.py

from __future__ import annotations

from fastapi import APIRouter, Request, Response

from app.api.forward_openai import forward_openai_request
from app.utils.logger import relay_log as logger

router = APIRouter(prefix="/v1", tags=["chatkit"])


# ---------------------------------------------------------------------------
# Sessions
# ---------------------------------------------------------------------------


@router.post("/chatkit/sessions")
async def create_chatkit_session(request: Request) -> Response:
    """
    Thin proxy:
    POST https://api.openai.com/v1/chatkit/sessions
    """
    logger.info(
        "Relay: create ChatKit session",
        extra={"path": "/v1/chatkit/sessions", "method": "POST"},
    )
    return await forward_openai_request(request)


@router.post("/chatkit/sessions/{session_id}/cancel")
async def cancel_chatkit_session(session_id: str, request: Request) -> Response:
    """
    Thin proxy:
    POST https://api.openai.com/v1/chatkit/sessions/{session_id}/cancel
    """
    logger.info(
        "Relay: cancel ChatKit session",
        extra={
            "path": f"/v1/chatkit/sessions/{session_id}/cancel",
            "method": "POST",
        },
    )
    return await forward_openai_request(request)


# ---------------------------------------------------------------------------
# Threads
# ---------------------------------------------------------------------------


@router.get("/chatkit/threads")
async def list_chatkit_threads(request: Request) -> Response:
    """
    Thin proxy:
    GET https://api.openai.com/v1/chatkit/threads
    """
    logger.info(
        "Relay: list ChatKit threads",
        extra={"path": "/v1/chatkit/threads", "method": "GET"},
    )
    return await forward_openai_request(request)


@router.post("/chatkit/threads")
async def create_chatkit_thread(request: Request) -> Response:
    """
    Thin proxy:
    POST https://api.openai.com/v1/chatkit/threads
    (The spec exposes thread creation; this forwards it unchanged.)
    """
    logger.info(
        "Relay: create ChatKit thread",
        extra={"path": "/v1/chatkit/threads", "method": "POST"},
    )
    return await forward_openai_request(request)


@router.get("/chatkit/threads/{thread_id}")
async def retrieve_chatkit_thread(thread_id: str, request: Request) -> Response:
    """
    Thin proxy:
    GET https://api.openai.com/v1/chatkit/threads/{thread_id}
    """
    logger.info(
        "Relay: retrieve ChatKit thread",
        extra={"path": f"/v1/chatkit/threads/{thread_id}", "method": "GET"},
    )
    return await forward_openai_request(request)


@router.delete("/chatkit/threads/{thread_id}")
async def delete_chatkit_thread(thread_id: str, request: Request) -> Response:
    """
    Thin proxy:
    DELETE https://api.openai.com/v1/chatkit/threads/{thread_id}
    """
    logger.info(
        "Relay: delete ChatKit thread",
        extra={"path": f"/v1/chatkit/threads/{thread_id}", "method": "DELETE"},
    )
    return await forward_openai_request(request)


@router.get("/chatkit/threads/{thread_id}/items")
async def list_chatkit_thread_items(thread_id: str, request: Request) -> Response:
    """
    Thin proxy:
    GET https://api.openai.com/v1/chatkit/threads/{thread_id}/items
    """
    logger.info(
        "Relay: list ChatKit thread items",
        extra={
            "path": f"/v1/chatkit/threads/{thread_id}/items",
            "method": "GET",
        },
    )
    return await forward_openai_request(request)
