from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel, Field

from app.api.forward_openai import forward_openai_method_path

router = APIRouter(prefix="/v1", tags=["proxy"])


class ProxyRequest(BaseModel):
    """
    Allowlisted proxy request.

    Back-compat:
      - Accept both "body" (preferred) and "json" (legacy examples) as the request payload.
    """
    method: str = Field(..., description="HTTP method to forward, e.g. GET/POST/DELETE")
    path: str = Field(..., description="Upstream path to call, e.g. /v1/models")
    query: Optional[Dict[str, Any]] = Field(default=None, description="Optional querystring parameters")
    body: Optional[Any] = Field(default=None, description="JSON body to send upstream")
    json: Optional[Any] = Field(default=None, description="Alias of body (legacy)")

    def resolved_body(self) -> Optional[Any]:
        return self.body if self.body is not None else self.json


_ALLOWLIST: List[Tuple[str, re.Pattern[str]]] = [
    ("GET", re.compile(r"^/v1/models$")),
    ("GET", re.compile(r"^/v1/models/[^/]+$")),
    ("POST", re.compile(r"^/v1/embeddings$")),
    ("POST", re.compile(r"^/v1/responses$")),
    ("GET", re.compile(r"^/v1/responses/[^/]+$")),
    ("DELETE", re.compile(r"^/v1/responses/[^/]+$")),
    ("POST", re.compile(r"^/v1/responses/[^/]+/cancel$")),
    ("GET", re.compile(r"^/v1/responses/[^/]+/input_items$")),
    ("GET", re.compile(r"^/v1/files$")),
    ("GET", re.compile(r"^/v1/files/[^/]+$")),
    ("DELETE", re.compile(r"^/v1/files/[^/]+$")),
    ("GET", re.compile(r"^/v1/vector_stores$")),
    ("POST", re.compile(r"^/v1/vector_stores$")),
    ("GET", re.compile(r"^/v1/vector_stores/[^/]+$")),
    ("DELETE", re.compile(r"^/v1/vector_stores/[^/]+$")),
    ("POST", re.compile(r"^/v1/vector_stores/[^/]+/file_batches$")),
    ("GET", re.compile(r"^/v1/vector_stores/[^/]+/file_batches/[^/]+$")),
    ("POST", re.compile(r"^/v1/vector_stores/[^/]+/file_batches/[^/]+/cancel$")),
    ("GET", re.compile(r"^/v1/vector_stores/[^/]+/files$")),
    ("POST", re.compile(r"^/v1/vector_stores/[^/]+/files$")),
    ("GET", re.compile(r"^/v1/vector_stores/[^/]+/files/[^/]+$")),
    ("DELETE", re.compile(r"^/v1/vector_stores/[^/]+/files/[^/]+$")),
    ("GET", re.compile(r"^/v1/containers$")),
    ("POST", re.compile(r"^/v1/containers$")),
    ("GET", re.compile(r"^/v1/containers/[^/]+$")),
    ("DELETE", re.compile(r"^/v1/containers/[^/]+$")),
    ("GET", re.compile(r"^/v1/containers/[^/]+/files$")),
    ("POST", re.compile(r"^/v1/containers/[^/]+/files$")),
    ("GET", re.compile(r"^/v1/containers/[^/]+/files/[^/]+$")),
    ("DELETE", re.compile(r"^/v1/containers/[^/]+/files/[^/]+$")),
    ("GET", re.compile(r"^/v1/conversations$")),
    ("POST", re.compile(r"^/v1/conversations$")),
    ("GET", re.compile(r"^/v1/conversations/[^/]+$")),
    ("DELETE", re.compile(r"^/v1/conversations/[^/]+$")),
]

_BLOCKED_PREFIXES = [
    "/v1/admin",
    "/v1/dashboard",
    "/v1/organization",
    "/v1/internal",
]


def _blocked_reason(method: str, path: str, body: Optional[Any]) -> Optional[str]:
    for prefix in _BLOCKED_PREFIXES:
        if path.startswith(prefix):
            return f"blocked prefix: {prefix}"

    if isinstance(body, dict) and body.get("stream") is True:
        return "stream=true not allowed via /v1/proxy; use /v1/responses:stream"

    for m, pat in _ALLOWLIST:
        if method == m and pat.match(path):
            return None

    return "method/path not allowlisted for /v1/proxy"


@router.post("/proxy")
async def proxy(call: ProxyRequest, request: Request) -> Response:
    method = (call.method or "").upper().strip()
    path = (call.path or "").strip()

    if not method or not path:
        raise HTTPException(status_code=400, detail="method and path are required")
    if not path.startswith("/"):
        path = "/" + path

    body = call.resolved_body()

    reason = _blocked_reason(method, path, body)
    if reason:
        raise HTTPException(status_code=403, detail=reason)

    return await forward_openai_method_path(
        method=method,
        path=path,
        query=call.query,
        json_body=body,
        inbound_headers=request.headers,
    )
