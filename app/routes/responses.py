from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.api.forward_openai import forward_openai_method_path, forward_openai_request
from app.core.config import get_settings

router = APIRouter(prefix="/v1", tags=["responses"])

_DISABLE_TOOLS_HEADER = "x-relay-disable-tools"


def _header_truthy(value: Optional[str]) -> bool:
    if value is None:
        return False
    v = value.strip().lower()
    return v in {"1", "true", "yes", "on"}


def _load_tools_manifest() -> List[Dict[str, Any]]:
    """
    Loads a list of tool definitions (dicts) from tools_manifest.json.

    Priority:
    1) Package-relative path: app/manifests/tools_manifest.json (common in this repo)
    2) CWD-relative path: tools_manifest.json (dev convenience)
    3) CWD-relative path: app/manifests/tools_manifest.json (dev convenience)
    """
    candidates: List[Path] = []

    # 1) Repo-style: app/manifests/tools_manifest.json next to code
    here = Path(__file__).resolve()
    # app/api/responses.py -> app/api -> app -> (siblings) manifests
    candidates.append(here.parents[1] / "manifests" / "tools_manifest.json")

    # 2) CWD fallback
    candidates.append(Path(os.getcwd()) / "tools_manifest.json")
    candidates.append(Path(os.getcwd()) / "app" / "manifests" / "tools_manifest.json")

    for p in candidates:
        try:
            if p.is_file():
                raw = p.read_text(encoding="utf-8")
                data = json.loads(raw)
                if isinstance(data, list):
                    # list of tool dicts
                    return [x for x in data if isinstance(x, dict)]
                if isinstance(data, dict):
                    # tolerate {"tools":[...]} or similar
                    maybe = data.get("tools")
                    if isinstance(maybe, list):
                        return [x for x in maybe if isinstance(x, dict)]
        except Exception:
            continue

    return []


TOOLS_MANIFEST: List[Dict[str, Any]] = _load_tools_manifest()


def _should_inject_tools(request: Request) -> bool:
    if not TOOLS_MANIFEST:
        return False
    if _header_truthy(request.headers.get(_DISABLE_TOOLS_HEADER)):
        return False
    return True


def _inject_tools_if_missing(payload: Dict[str, Any], request: Request) -> Dict[str, Any]:
    """
    Inject tool definitions into a /v1/responses request only if:
    - injection is enabled, and
    - caller did NOT provide a "tools" field (or tools is None)
    """
    if not _should_inject_tools(request):
        return payload
    if "tools" in payload and payload["tools"] is not None:
        return payload

    out = dict(payload)
    out["tools"] = TOOLS_MANIFEST
    return out


@router.post("/responses")
async def create_response(request: Request):
    """
    POST /v1/responses
    - Parses JSON body if present.
    - Injects tools_manifest.json definitions if caller did not provide tools.
    - For non-JSON bodies, falls back to passthrough.
    """
    raw = await request.body()
    if not raw:
        return await forward_openai_request(request)

    try:
        body = json.loads(raw.decode("utf-8"))
    except Exception:
        return await forward_openai_request(request)

    if isinstance(body, dict):
        body = _inject_tools_if_missing(body, request)
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
    Pure passthrough to upstream.
    This endpoint must exist to prevent relay-level 404.
    """
    return await forward_openai_request(request)


@router.post("/responses/{response_id}/cancel")
async def cancel_response(response_id: str, request: Request):
    """
    POST /v1/responses/{response_id}/cancel
    Pure passthrough to upstream.
    """
    return await forward_openai_request(request)


@router.get("/responses/{response_id}/input_items")
async def list_response_input_items(response_id: str, request: Request):
    """
    GET /v1/responses/{response_id}/input_items
    Pure passthrough to upstream.
    """
    return await forward_openai_request(request)


class ResponsesCompactRequest(BaseModel):
    """
    Action-friendly /responses wrapper.

    - Accepts simplified schema used by Actions.
    - Forwards to /v1/responses.
    - Injects tools manifest if caller didn't provide tools.
    """

    model: Optional[str] = Field(default=None)
    input: Any = Field(...)
    instructions: Optional[str] = Field(default=None)
    max_output_tokens: Optional[int] = Field(default=None)
    temperature: Optional[float] = Field(default=None)
    top_p: Optional[float] = Field(default=None)

    # Pass-through support (optional)
    tools: Optional[Any] = Field(default=None)
    tool_choice: Optional[Any] = Field(default=None)


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

    if payload.tools is not None:
        req["tools"] = payload.tools
    if payload.tool_choice is not None:
        req["tool_choice"] = payload.tool_choice

    req = _inject_tools_if_missing(req, request)

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
