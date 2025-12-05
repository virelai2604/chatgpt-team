# app/routes/responses.py

from __future__ import annotations

from fastapi import APIRouter, Request, Response

from app.api.forward_openai import forward_openai_request
from app.utils.logger import relay_log as logger

router = APIRouter(prefix="/v1", tags=["responses"])


@router.post("/responses")
async def create_response(request: Request) -> Response:
    """
    POST /v1/responses

    Create a model response (core Responses API entrypoint).
    """
    logger.info("→ [responses] POST %s", request.url.path)
    return await forward_openai_request(request)


@router.get("/responses/{response_id}")
async def retrieve_response(response_id: str, request: Request) -> Response:
    """
    GET /v1/responses/{response_id}

    Retrieve a single model response by ID.
    """
    logger.info("→ [responses] GET %s", request.url.path)
    return await forward_openai_request(request)


@router.delete("/responses/{response_id}")
async def delete_response(response_id: str, request: Request) -> Response:
    """
    DELETE /v1/responses/{response_id}

    Delete a response by ID.
    """
    logger.info("→ [responses] DELETE %s", request.url.path)
    return await forward_openai_request(request)


@router.post("/responses/{response_id}/cancel")
async def cancel_response(response_id: str, request: Request) -> Response:
    """
    POST /v1/responses/{response_id}/cancel

    Cancel a background response.
    """
    logger.info("→ [responses] POST %s", request.url.path)
    return await forward_openai_request(request)


@router.get("/responses/{response_id}/input_items")
async def list_response_input_items(
    response_id: str,
    request: Request,
) -> Response:
    """
    GET /v1/responses/{response_id}/input_items

    List input items that were used to generate this response.
    """
    logger.info("→ [responses] GET %s", request.url.path)
    return await forward_openai_request(request)


@router.post("/responses/input_tokens")
async def get_input_token_counts(request: Request) -> Response:
    """
    POST /v1/responses/input_tokens

    Compute input token counts for a hypothetical response request.
    """
    logger.info("→ [responses] POST %s", request.url.path)
    return await forward_openai_request(request)
