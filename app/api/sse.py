from __future__ import annotations

from typing import Any, Dict, cast

from fastapi import APIRouter, Request, Response

from app.api.forward_openai import forward_openai_method_path

router = APIRouter(prefix="/v1", tags=["sse"])
actions_router = APIRouter(prefix="/v1/actions/responses", tags=["responses_actions"])


@router.post("/responses:stream")
async def responses_stream(request: Request) -> Response:
    """
    Map POST /v1/responses:stream -> upstream POST /v1/responses with stream enabled.
    """
    body: Any = await request.json()
    if not isinstance(body, dict):
        body = {"input": body}

    body.setdefault("stream", True)

    return await forward_openai_method_path(
        request=request,
        method="POST",
        path="/v1/responses",
        inbound_headers=request.headers,
        json_body=cast(Dict[str, Any], body),
    )


@actions_router.post(
    "/stream",
    operation_id="actionsResponsesStream",
    summary="Actions wrapper for /v1/responses:stream (SSE)",
)
async def actions_responses_stream(request: Request) -> Response:
    """
    Actions-friendly SSE stream wrapper.

    Accepts JSON input and forwards to /v1/responses with stream enabled.
    """
    body: Any = await request.json()
    if not isinstance(body, dict):
        body = {"input": body}

    body.setdefault("stream", True)

    return await forward_openai_method_path(
        request=request,
        method="POST",
        path="/v1/responses",
        inbound_headers=request.headers,
        json_body=cast(Dict[str, Any], body),
    )