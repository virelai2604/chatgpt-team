from __future__ import annotations

import re
from typing import Any, Mapping, Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response
from pydantic import AliasChoices, BaseModel, Field, model_validator

from app.api.forward_openai import forward_openai_method_path
from app.core.auth import require_relay_auth
from app.utils.logger import relay_log

router = APIRouter(prefix="/v1", tags=["proxy"])

# -----------------------------------------------------------------------------
# Proxy policy
#
# This endpoint is intentionally restricted: it only forwards a curated subset
# of OpenAI routes and blocks internal/admin routes.
# -----------------------------------------------------------------------------

_BLOCKED_PREFIXES = (
    "/v1/admin",
    "/admin",
    "/internal",
    "/v1/internal",
)

# Each entry: (allowed_methods, regex_pattern)
_ALLOWED_ROUTES: list[tuple[set[str], re.Pattern[str]]] = [
    # ---- Responses (metadata only; streaming handled via /v1/responses route) ----
    ({"POST"}, re.compile(r"^/v1/responses$")),
    ({"GET"}, re.compile(r"^/v1/responses/[^/]+$")),
    ({"DELETE"}, re.compile(r"^/v1/responses/[^/]+$")),
    ({"POST"}, re.compile(r"^/v1/responses/[^/]+/cancel$")),

    # ---- Embeddings ----
    ({"POST"}, re.compile(r"^/v1/embeddings$")),

    # ---- Models ----
    ({"GET"}, re.compile(r"^/v1/models$")),
    ({"GET"}, re.compile(r"^/v1/models/[^/]+$")),

    # ---- Files (metadata only; binary content handled by /v1/files routes) ----
    ({"GET"}, re.compile(r"^/v1/files$")),
    ({"GET"}, re.compile(r"^/v1/files/[^/]+$")),
    ({"DELETE"}, re.compile(r"^/v1/files/[^/]+$")),

    # ---- Vector stores (metadata only) ----
    ({"GET", "POST"}, re.compile(r"^/v1/vector_stores$")),
    ({"GET", "POST", "DELETE"}, re.compile(r"^/v1/vector_stores/[^/]+$")),

    # ---- Containers (metadata only) ----
    ({"GET", "POST"}, re.compile(r"^/v1/containers$")),
    ({"GET", "POST", "DELETE"}, re.compile(r"^/v1/containers/[^/]+$")),

    # ---- Conversations (metadata only) ----
    ({"POST"}, re.compile(r"^/v1/conversations$")),
    ({"GET"}, re.compile(r"^/v1/conversations/[^/]+$")),
    ({"DELETE"}, re.compile(r"^/v1/conversations/[^/]+$")),

    # ---- Batches (metadata only) ----
    ({"GET", "POST"}, re.compile(r"^/v1/batches$")),
    ({"GET"}, re.compile(r"^/v1/batches/[^/]+$")),
    ({"POST"}, re.compile(r"^/v1/batches/[^/]+/cancel$")),

    # ---- Videos (metadata only; create/content are handled by /v1/videos routes) ----
    ({"GET"}, re.compile(r"^/v1/videos$")),
    ({"GET"}, re.compile(r"^/v1/videos/[^/]+$")),
    ({"POST"}, re.compile(r"^/v1/videos/[^/]+/remix$")),
    ({"DELETE"}, re.compile(r"^/v1/videos/[^/]+$")),
]


def _is_blocked(path: str) -> bool:
    p = (path or "").strip()
    return any(p.startswith(prefix) for prefix in _BLOCKED_PREFIXES)


def _is_allowed(method: str, path: str) -> bool:
    m = (method or "").upper().strip()
    p = (path or "").strip()
    for allowed_methods, pattern in _ALLOWED_ROUTES:
        if m in allowed_methods and pattern.match(p):
            return True
    return False


class ProxyRequest(BaseModel):
    method: str = Field(..., description="HTTP method to call upstream (GET/POST/DELETE/...)")
    path: str = Field(..., description="Upstream OpenAI path, e.g. /v1/videos/...")
    query: Optional[Mapping[str, Any]] = Field(default=None, description="Query params to send upstream")

    # Accept body under multiple common names
    body: Optional[Any] = Field(
        default=None,
        validation_alias=AliasChoices("body", "json", "payload"),
        description="JSON body (optional)",
    )

    @model_validator(mode="after")
    def _normalize(self) -> "ProxyRequest":
        self.method = (self.method or "").upper().strip()
        self.path = (self.path or "").strip()
        return self


@router.post("/proxy")
async def proxy(call: ProxyRequest, request: Request) -> Response:
    require_relay_auth(request)

    if _is_blocked(call.path):
        raise HTTPException(status_code=403, detail="Path blocked by policy")

    if not _is_allowed(call.method, call.path):
        raise HTTPException(status_code=403, detail="Route not allowlisted for proxy")

    relay_log.info("Proxy call: %s %s", call.method, call.path)

    return await forward_openai_method_path(
        method=call.method,
        path=call.path,
        query=call.query,
        json_body=call.body,
        inbound_headers=request.headers,
    )
