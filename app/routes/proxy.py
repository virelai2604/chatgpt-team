from __future__ import annotations

import re
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, Field

from app.api.forward_openai import forward_openai_method_path

router = APIRouter(prefix="/v1", tags=["proxy"])


class ProxyRequest(BaseModel):
    """
    Action-friendly proxy envelope.

    IMPORTANT: This is intentionally constrained to JSON requests.
    For streaming (SSE), websockets, multipart uploads, and binary downloads, use
    explicit relay routes instead of /v1/proxy.
    """
    method: str = Field(..., description="HTTP method: GET, POST, PUT, PATCH, DELETE")
    path: str = Field(..., description="Upstream OpenAI path, e.g. /v1/responses")
    query: Optional[Dict[str, Any]] = Field(
        default=None, description="Query parameters (object/dict)"
    )
    body: Optional[Any] = Field(
        default=None, description="JSON body for POST/PUT/PATCH"
    )


_ALLOWED_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE"}

# Block obvious non-Action-safe families (websocket, multipart-heavy, etc.)
_BLOCKED_PREFIXES = (
    "/v1/realtime",  # websocket
    "/v1/audio",     # often multipart/binary
    "/v1/uploads",   # multipart / resumable
)

# Block direct recursion or local-only helper endpoints
_BLOCKED_PATHS = {
    "/v1/proxy",
    "/v1/responses:stream",
}

# Multipart endpoints that won't work via JSON envelope
_BLOCKED_METHOD_PATH_REGEX = {
    ("POST", re.compile(r"^/v1/files$")),
    ("POST", re.compile(r"^/v1/images/(edits|variations)$")),
}


def _normalize_path(path: str) -> str:
    p = (path or "").strip()

    if not p:
        raise HTTPException(status_code=400, detail="path is required")

    # Disallow full URLs; only allow paths.
    if "://" in p or p.lower().startswith("http"):
        raise HTTPException(status_code=400, detail="path must be an OpenAI API path, not a URL")

    # Disallow embedding query string in the path (use `query` field).
    if "?" in p:
        raise HTTPException(status_code=400, detail="path must not include '?'; use `query` field")

    # Ensure leading slash
    if not p.startswith("/"):
        p = "/" + p

    # Ensure /v1 prefix
    if p.startswith("/v1"):
        normalized = p
    elif p.startswith("v1/"):
        normalized = "/" + p
    else:
        normalized = "/v1" + p

    # Collapse accidental double slashes (defense-in-depth)
    while "//" in normalized:
        normalized = normalized.replace("//", "/")

    return normalized


def _blocked_reason(method: str, path: str, body: Any) -> Optional[str]:
    # No streaming via proxy envelope; Actions typically can't handle SSE well.
    if isinstance(body, dict) and body.get("stream") is True:
        return "stream=true is not allowed via /v1/proxy (use explicit streaming route)"

    # Block `:something` style paths
    if ":" in path:
        return "':' paths are not allowed via /v1/proxy"

    # Basic traversal / weirdness guards
    if ".." in path or "#" in path:
        return "path contains illegal sequences"
    if any(ch.isspace() for ch in path):
        return "path must not contain whitespace"

    if path in _BLOCKED_PATHS:
        return "path is blocked"

    for prefix in _BLOCKED_PREFIXES:
        if path.startswith(prefix):
            return "path prefix is blocked"

    # Block binary downloads by default (Action-unfriendly)
    if path.endswith("/content"):
        return "binary /content endpoints are not allowed via /v1/proxy"

    for (m, rx) in _BLOCKED_METHOD_PATH_REGEX:
        if method == m and rx.match(path):
            return "multipart endpoint blocked via /v1/proxy"

    return None


@router.post("/proxy")
async def proxy(call: ProxyRequest, request: Request) -> Response:
    method = (call.method or "").strip().upper()
    if method not in _ALLOWED_METHODS:
        raise HTTPException(status_code=400, detail=f"Unsupported method: {call.method}")

    path = _normalize_path(call.path)

    reason = _blocked_reason(method, path, call.body)
    if reason:
        raise HTTPException(status_code=403, detail=reason)

    return await forward_openai_method_path(
        method=method,
        path=path,
        query=call.query,
        json_body=call.body,
        inbound_headers=request.headers,
    )
