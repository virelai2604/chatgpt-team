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

_DISABLE_TOOLS_HEADER = "x-relay-disable-tools"
_SETTINGS = get_settings()

def _header_truthy(value: Optional[str]) -> bool:
    if value is None:
        return False
    v = value.strip().lower()
    return v in {"1", "true", "yes", "on"}

def _project_root() -> Path:
    """Locate project root (two levels above this module)."""
    here = Path(__file__).resolve()
    return here.parents[2] if len(here.parents) >= 3 else here.parents[1]

def _resolve_tools_manifest_path() -> Optional[Path]:
    """
    Resolve settings.TOOLS_MANIFEST into an absolute path.
    Supports absolute, repo-relative, and root-relative forms.
    """
    raw = (getattr(_SETTINGS, "TOOLS_MANIFEST", "") or "").strip()
    if not raw:
        return None
    p = Path(raw)
    if p.is_absolute():
        return p
    root = _project_root()
    # If path starts with "app/", assume repo-relative
    if raw.startswith("app/") or raw.startswith("app\\"):
        return root / raw
    return root / raw

def _load_tools_manifest() -> List[Dict[str, Any]]:
    """
    Read JSON from the tools manifest file.
    Accepts either a list of tool dicts or {"tools":[…]}.
    Returns [] if file missing or malformed.
    """
    path = _resolve_tools_manifest_path()
    if not path or not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return [x for x in data if isinstance(x, dict)]
        if isinstance(data, dict):
            maybe = data.get("tools")
            if isinstance(maybe, list):
                return [x for x in maybe if isinstance(x, dict)]
    except Exception:
        pass
    return []

TOOLS_MANIFEST: List[Dict[str, Any]] = _load_tools_manifest()

def _should_inject_tools(request: Request) -> bool:
    """Return True if tools should be auto-injected."""
    if not TOOLS_MANIFEST:
        return False
    if _header_truthy(request.headers.get(_DISABLE_TOOLS_HEADER)):
        return False
    return True

def _inject_tools_if_missing(payload: Dict[str, Any], request: Request) -> Dict[str, Any]:
    """
    Inject tools into the request only if caller omitted 'tools' (or set it to None)
    and injection is enabled.
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
        data = json.loads(upstream_response.body.decode("utf-8"))
    except Exception:
        return upstream_response
    if isinstance(data, dict):
        data["object"] = "response.compaction"
    return JSONResponse(content=data, status_code=upstream_response.status_code)
