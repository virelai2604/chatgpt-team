# app/routes/chatkit.py

from __future__ import annotations

from fastapi import APIRouter, Request

from app.api.forward_openai import forward_openai_request

router = APIRouter(tags=["chatkit"])


# Sessions

@router.post("/v1/chatkit/sessions")
async def create_chatkit_session(request: Request):
    """
    Proxy for: POST https://api.openai.com/v1/chatkit/sessions
    """
    return await forward_openai_request(request)


@router.get("/v1/chatkit/sessions/{session_id}")
async def retrieve_chatkit_session(request: Request, session_id: str):
    """
    Proxy for: GET https://api.openai.com/v1/chatkit/sessions/{session_id}
    """
    return await forward_openai_request(request)


# Threads

@router.post("/v1/chatkit/threads")
async def create_chatkit_thread(request: Request):
    """
    Proxy for: POST https://api.openai.com/v1/chatkit/threads
    """
    return await forward_openai_request(request)


@router.get("/v1/chatkit/threads/{thread_id}")
async def retrieve_chatkit_thread(request: Request, thread_id: str):
    """
    Proxy for: GET https://api.openai.com/v1/chatkit/threads/{thread_id}
    """
    return await forward_openai_request(request)


@router.get("/v1/chatkit/threads/{thread_id}/items")
async def list_chatkit_thread_items(request: Request, thread_id: str):
    """
    Proxy for: GET https://api.openai.com/v1/chatkit/threads/{thread_id}/items
    """
    return await forward_openai_request(request)


@router.post("/v1/chatkit/threads/{thread_id}/items")
async def append_chatkit_thread_items(request: Request, thread_id: str):
    """
    Proxy for: POST https://api.openai.com/v1/chatkit/threads/{thread_id}/items
    """
    return await forward_openai_request(request)
