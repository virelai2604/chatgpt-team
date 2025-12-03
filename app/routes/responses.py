# app/routes/responses.py

from __future__ import annotations

from fastapi import APIRouter, Request, Response

from app.api.forward_openai import forward_openai_request

router = APIRouter(
    prefix="/v1",
    tags=["responses"],
)


@router.post("/responses")
async def create_response(request: Request) -> Response:
    """
    /v1/responses create endpoint.

    SSE streaming is handled inside forward_openai_request when:
      - Accept: text/event-stream, or
      - body.stream == true
    """
    return await forward_openai_request(request)


@router.get("/responses/{response_id}")
async def retrieve_response(response_id: str, request: Request) -> Response:
    return await forward_openai_request(request)


@router.delete("/responses/{response_id}")
async def delete_response(response_id: str, request: Request) -> Response:
    return await forward_openai_request(request)


@router.post("/responses/{response_id}/cancel")
async def cancel_response(response_id: str, request: Request) -> Response:
    return await forward_openai_request(request)


@router.get("/responses/{response_id}/input_token_counts")
async def response_input_token_counts(response_id: str, request: Request) -> Response:
    return await forward_openai_request(request)


@router.get("/responses/{response_id}/items")
async def list_response_items(response_id: str, request: Request) -> Response:
    return await forward_openai_request(request)
