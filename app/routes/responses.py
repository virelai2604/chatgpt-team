from __future__ import annotations

import json
from typing import Any, Dict

from fastapi import APIRouter, Body, Request
from fastapi.responses import JSONResponse, Response
from starlette.responses import StreamingResponse

from app.api.forward_openai import forward_openai_method_path, forward_openai_request

router = APIRouter(prefix="/v1", tags=["responses"])


@router.post("/responses")
async def create_response(request: Request) -> Response:
    """
    Forward /v1/responses to OpenAI.

    - Non-stream: returns JSON response as-is
    - Stream (SSE): forward_openai_request will detect upstream text/event-stream and return a StreamingResponse

    This avoids the historical bug where a StreamingResponse was wrapped inside another StreamingResponse
    (TypeError: 'StreamingSSE' object is not iterable).
    """
    return await forward_openai_request(request)


@router.post("/responses/compact")
async def create_response_compact(
    request: Request,
    body: Dict[str, Any] = Body(...),
) -> Response:
    """
    Custom helper endpoint used by local tests/tools.

    Behavior:
      - Forces a non-streaming OpenAI /v1/responses call
      - Injects metadata.compact as a *string* (OpenAI metadata values must be strings)
      - Wraps the upstream response into:
          {
            "object": "response.compaction",
            "original": <OpenAI response payload>
          }
    """
    payload: Dict[str, Any] = dict(body) if isinstance(body, dict) else {}

    # Ensure this helper endpoint is non-streaming.
    payload.pop("stream", None)

    # OpenAI metadata values must be strings; normalize metadata and force "compact".
    metadata = payload.get("metadata")
    if not isinstance(metadata, dict):
        metadata = {}
    else:
        # shallow copy to avoid mutating caller-owned dict
        metadata = dict(metadata)

    # Normalize metadata values to strings (defensive; OpenAI expects string values).
    normalized_metadata: Dict[str, str] = {str(k): str(v) for k, v in metadata.items()}
    normalized_metadata["compact"] = "true"
    payload["metadata"] = normalized_metadata

    upstream = await forward_openai_method_path(
        "POST",
        "/v1/responses",
        json_body=payload,
        inbound_headers=request.headers,
    )

    # If upstream errored, preserve the error contract exactly.
    if getattr(upstream, "status_code", 200) >= 400:
        return upstream

    # If somehow streamed, just pass-through (unexpected for this helper).
    if isinstance(upstream, StreamingResponse):
        return upstream

    raw = getattr(upstream, "body", b"") or b""
    try:
        original = json.loads(raw.decode("utf-8")) if raw else None
    except Exception:
        # If parsing fails, pass-through the upstream response.
        return upstream

    compaction = {
        "object": "response.compaction",
        "original": original,
    }
    return JSONResponse(content=compaction, status_code=upstream.status_code)


@router.get("/responses/{response_id}")
async def retrieve_response(request: Request, response_id: str) -> Response:
    return await forward_openai_request(request)


@router.delete("/responses/{response_id}")
async def delete_response(request: Request, response_id: str) -> Response:
    return await forward_openai_request(request)


@router.post("/responses/{response_id}/cancel")
async def cancel_response(request: Request, response_id: str) -> Response:
    return await forward_openai_request(request)


@router.get("/responses/{response_id}/input_items")
async def list_response_input_items(request: Request, response_id: str) -> Response:
    return await forward_openai_request(request)
