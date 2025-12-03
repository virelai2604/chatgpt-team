from __future__ import annotations

import logging

from fastapi import APIRouter, Request, Response

from app.api.forward_openai import forward_openai_request

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/v1",
    tags=["responses"],
)


@router.post("/responses")
async def create_response(request: Request) -> Response:
    """
    POST /v1/responses

    Create a model response.
    Mirrors:
    https://platform.openai.com/docs/api-reference/responses/create
    """
    logger.debug("Proxying POST /v1/responses to OpenAI")
    return await forward_openai_request(request)


@router.get("/responses/{response_id}")
async def retrieve_response(response_id: str, request: Request) -> Response:
    """
    GET /v1/responses/{response_id}

    Retrieve a response.
    Mirrors:
    https://platform.openai.com/docs/api-reference/responses/retrieve
    """
    logger.debug("Proxying GET /v1/responses/%s to OpenAI", response_id)
    return await forward_openai_request(request)


@router.delete("/responses/{response_id}")
async def delete_response(response_id: str, request: Request) -> Response:
    """
    DELETE /v1/responses/{response_id}

    Delete a response.
    Mirrors:
    https://platform.openai.com/docs/api-reference/responses/delete
    """
    logger.debug("Proxying DELETE /v1/responses/%s to OpenAI", response_id)
    return await forward_openai_request(request)


@router.post("/responses/{response_id}/cancel")
async def cancel_response(response_id: str, request: Request) -> Response:
    """
    POST /v1/responses/{response_id}/cancel

    Cancel a response in progress.
    Mirrors:
    https://platform.openai.com/docs/api-reference/responses/cancel
    """
    logger.debug("Proxying POST /v1/responses/%s/cancel to OpenAI", response_id)
    return await forward_openai_request(request)


@router.api_route(
    "/responses/{response_id}/{subpath:path}",
    methods=["GET", "POST"],
)
async def proxy_response_subroutes(
    response_id: str,
    subpath: str,
    request: Request,
) -> Response:
    """
    Generic proxy for any nested Responses sub-routes, such as:

    - /v1/responses/{response_id}/items
    - /v1/responses/{response_id}/input-token-counts
    - Any new future subpaths

    This ensures we automatically cover:
    https://platform.openai.com/docs/api-reference/responses/list-items
    https://platform.openai.com/docs/api-reference/responses/get-input-token-counts
    and any similar additions.
    """
    logger.debug(
        "Proxying %s %s to OpenAI (response_id=%s, subpath=%s)",
        request.method,
        request.url.path,
        response_id,
        subpath,
    )
    return await forward_openai_request(request)
