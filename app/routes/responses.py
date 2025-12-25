from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter, Body, Request
from fastapi.responses import JSONResponse
from starlette.responses import Response, StreamingResponse

from app.api.forward_openai import forward_openai_method_path, forward_openai_request
from app.core.config import get_settings

router = APIRouter(prefix="/v1", tags=["responses"])


@router.post("/responses")
async def create_response(request: Request) -> Response:
    """
    Pass-through proxy to OpenAI Responses API.
    Supports non-streaming JSON and streaming (SSE) when `stream: true`.
    """
    return await forward_openai_request(request)


@router.post("/responses/compact")
async def create_response_compact(
    request: Request,
    body: Dict[str, Any] = Body(...),
) -> Response:
    """
    Relay-only wrapper:
      - normalizes input into a list
      - ensures default model if missing
      - sets metadata.compact=true
      - forwards to POST /v1/responses upstream
      - wraps upstream JSON:

        {
          "object": "response.compaction",
          "data": <upstream JSON>,
          "meta": { "model": "...", "compact": true, "timestamp": "..." }
        }
    """
    settings = get_settings()

    payload: Dict[str, Any] = dict(body or {})
    payload.pop("stream", None)  # compact is always non-streaming

    if "input" in payload and not isinstance(payload["input"], list):
        payload["input"] = [payload["input"]]

    if not payload.get("model"):
        payload["model"] = settings.DEFAULT_MODEL

    metadata = payload.get("metadata")
    if not isinstance(metadata, dict):
        metadata = {}
    else:
        metadata = dict(metadata)

    normalized_metadata = {str(k): str(v) for k, v in metadata.items()}
    normalized_metadata["compact"] = "true"
    payload["metadata"] = normalized_metadata

    upstream = await forward_openai_method_path(
        "POST",
        "/v1/responses",
        json_body=payload,
        inbound_headers=request.headers,
    )

    if upstream.status_code >= 400 or isinstance(upstream, StreamingResponse):
        return upstream

    raw = getattr(upstream, "body", b"") or b""
    try:
        upstream_json = json.loads(raw.decode("utf-8")) if raw else {}
    except Exception:
        return upstream

    wrapper = {
        "object": "response.compaction",
        "data": upstream_json,
        "meta": {
            "model": payload.get("model"),
            "compact": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    }
    return JSONResponse(content=wrapper, status_code=upstream.status_code)


@router.get("/responses/{response_id}/input_items")
async def list_response_input_items(response_id: str, request: Request) -> Response:
    return await forward_openai_request(request)


@router.post("/responses/{response_id}/cancel")
async def cancel_response(response_id: str, request: Request) -> Response:
    return await forward_openai_request(request)


@router.get("/responses/{response_id}")
async def retrieve_response(response_id: str, request: Request) -> Response:
    return await forward_openai_request(request)


@router.delete("/responses/{response_id}")
async def delete_response(response_id: str, request: Request) -> Response:
    return await forward_openai_request(request)
