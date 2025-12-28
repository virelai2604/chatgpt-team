from __future__ import annotations

import json
from typing import Any, Dict, Optional

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.api.forward_openai import forward_openai_method_path, forward_openai_request
from app.core.config import get_settings

router = APIRouter(prefix="/v1", tags=["responses"])


@router.post("/responses")
async def create_response(request: Request):
    return await forward_openai_request(request)


class ResponsesCompactRequest(BaseModel):
    """
    Action-friendly /responses wrapper.

    - Accepts a simplified schema commonly used by ChatGPT custom actions.
    - Produces a standard Responses API call to /v1/responses.
    """

    model: Optional[str] = Field(default=None)
    input: Any = Field(...)
    instructions: Optional[str] = Field(default=None)
    max_output_tokens: Optional[int] = Field(default=None)
    temperature: Optional[float] = Field(default=None)
    top_p: Optional[float] = Field(default=None)


@router.post("/responses/compact")
async def responses_compact(payload: ResponsesCompactRequest, request: Request):
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
        payload_data = json.loads(upstream_response.body.decode("utf-8"))
    except Exception:
        return upstream_response
    if isinstance(payload_data, dict):
        payload_data["object"] = "response.compaction"
    return JSONResponse(content=payload_data, status_code=upstream_response.status_code)