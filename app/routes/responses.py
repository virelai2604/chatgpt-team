from __future__ import annotations

from fastapi import APIRouter, Request, Response

from app.api.forward_openai import forward_openai_request

router = APIRouter(tags=["responses"])


@router.post("/v1/responses")
async def create_response(request: Request) -> Response:
    """
    POST /v1/responses

    Thin proxy to the OpenAI Responses API.
    Streaming is controlled via the 'stream' field in the JSON body
    and handled inside forward_openai_request.
    """
    return await forward_openai_request(request)


@router.get("/v1/responses")
async def list_responses(request: Request) -> Response:
    """
    GET /v1/responses
    """
    return await forward_openai_request(request)


@router.get("/v1/responses/{response_id}")
async def retrieve_response(response_id: str, request: Request) -> Response:
    """
    GET /v1/responses/{response_id}
    """
    return await forward_openai_request(request)


@router.post("/v1/responses/{response_id}/cancel")
async def cancel_response(response_id: str, request: Request) -> Response:
    """
    POST /v1/responses/{response_id}/cancel
    """
    return await forward_openai_request(request)
