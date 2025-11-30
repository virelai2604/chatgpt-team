# app/routes/conversations.py
from __future__ import annotations

from fastapi import APIRouter, Request, Response
from app.api.forward_openai import forward_openai_request

router = APIRouter(
    prefix="/v1",
    tags=["conversations"],
)


@router.get("/conversations")
async def list_conversations(request: Request) -> Response:
    return await forward_openai_request(request)


@router.post("/conversations")
async def create_conversation(request: Request) -> Response:
    return await forward_openai_request(request)


@router.get("/conversations/{conversation_id}")
async def retrieve_conversation(conversation_id: str, request: Request) -> Response:
    return await forward_openai_request(request)
