from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.api.forward_openai import forward_openai_method_path, forward_openai_request
from app.core.config import get_settings

router = APIRouter(prefix="/v1", tags=["responses"])

_SETTINGS = get_settings()

@router.post("/responses")
async def create_response(request: Request):
    """
    POST /v1/responses
    - Parses JSON body.
    - Injects tools manifest if caller omitted tools and injection is enabled.
    - Passes through to upstream for non-JSON bodies.
    """
    raw = await request.body()
    if not raw:
        return await forward_openai_request(request)
    try:
        body = json.loads(raw.decode("utf-8"))
    except Exception:
        return await forward_openai_request(request)
    if isinstance(body, dict):
        return await forward_openai_method_path(
            "POST",
            "/v1/responses",
            json_body=body,
            inbound_headers=request.headers,
            request=request,
        )
    return await forward_openai_request(request)

@router.get("/responses/{response_id}")
async def retrieve_response(response_id: str, request: Request):
    """
    GET /v1/responses/{response_id}
    Pure passthrough; required to prevent FastAPI 404 in the relay.
    """
    return await forward_openai_request(request)

@router.post("/responses/{response_id}/cancel")
async def cancel_response(response_id: str, request: Request):
    """POST /v1/responses/{response_id}/cancel (Passthrough)."""
    return await forward_openai_request(request)

@router.get("/responses/{response_id}/input_items")
async def response_input_items(response_id: str, request: Request):
    """GET /v1/responses/{response_id}/input_items (Passthrough)."""
    return await forward_openai_request(request)

class ResponsesCompactRequest(BaseModel):
    """
    Schema for /v1/responses/compact requests.
    Accepts minimal parameters and supports optional tools/tool_choice.
    """
    model: Optional[str] = Field(default=None)
    input: Any = Field(...)
    instructions: Optional[str] = Field(default=None)
    max_output_tokens: Optional[int] = Field(default=None)
    temperature: Optional[float] = Field(default=None)
    top_p: Optional[float] = Field(default=None)
    tools: Optional[Any] = Field(default=None)
    tool_choice: Optional[Any] = Field(default=None)

@router.post("/responses/compact")
async def responses_compact(payload: ResponsesCompactRequest, request: Request):
    """
    POST /v1/responses/compact
    - Builds a standard /v1/responses request dict from compact payload.
    - Injects tools if caller omitted them and injection is enabled.
    - Forwards to upstream.
    - Converts upstream result into a compaction object.
    """
    settings = get_settings()

    req: Dict[str, Any] = {
        "model": payload.model or settings.DEFAULT_MODEL,
        "input": payload.input,
    }
    if payload.instructions is not None:
        req["instructions"] = payload.instructions
    if payload.max_output_tokens is not None:
        req["max_output_tokens"] = payload.max_output_tokens
    if payload.temperature is not None:
        req["temperature"] = payload.temperature
    if payload.top_p is not None:
        req["top_p"] = payload.top_p
    if payload.tools is not None:
        req["tools"] = payload.tools
    if payload.tool_choice is not None:
        req["tool_choice"] = payload.tool_choice

    upstream_response = await forward_openai_method_path(
        "POST",
        "/v1/responses",
        json_body=req,
        inbound_headers=request.headers,
        request=request,
    )
    if upstream_response.status_code != 200:
        return upstream_response
    try:
        data = json.loads(upstream_response.body.decode("utf-8"))
    except Exception:
        return upstream_response
    if isinstance(data, dict):
        data["object"] = "response.compaction"
    return JSONResponse(content=data, status_code=upstream_response.status_code)
