from __future__ import annotations

import re
from typing import Any, Dict, Optional, Set, Tuple

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import AliasChoices, BaseModel, ConfigDict, Field, model_validator

from app.api.forward_openai import forward_openai_method_path

router = APIRouter(prefix="/v1", tags=["proxy"])


class ProxyRequest(BaseModel):
    """
    Action-friendly proxy envelope.

    Notes:
    - We intentionally do NOT use a field named `json`, because it shadows BaseModel.json().
    - For backward compatibility, we still ACCEPT an input key named "json" as an alias to `body`.
    """

    model_config = ConfigDict(extra="forbid")

    method: str = Field(..., description="HTTP method: GET, POST, PUT, PATCH, DELETE")
    path: str = Field(..., description="Upstream OpenAI path, e.g. /v1/responses")

    query: Optional[Dict[str, Any]] = Field(
        default=None,
        validation_alias=AliasChoices("query", "params", "query_params"),
        description="Query parameters (object/dict)",
    )

    body: Optional[Any] = Field(
        default=None,
        validation_alias=AliasChoices("body", "json", "json_body"),
        description="JSON body for POST/PUT/PATCH requests",
    )

    @model_validator(mode="after")
    def _avoid_empty_json_body_parse_errors(self) -> "ProxyRequest":
        m = (self.method or "").strip().upper()
        if m in {"POST", "PUT", "PATCH"} and self.body is None:
            self.body = {}
        return self


_ALLOWED_METHODS: Set[str] = {"GET", "POST", "PUT", "PATCH", "DELETE"}

_BLOCKED_PREFIXES: Tuple[str, ...] = (
    "/v1/admin",
    "/v1/webhooks",
    "/v1/moderations",
    "/v1/realtime",  # websocket family (not Actions-friendly)
    "/v1/uploads",  # multipart/resumable (use explicit wrapper routes)
    "/v1/audio",  # often multipart/binary
)

_BLOCKED_PATHS: Set[str] = {
    "/v1/proxy",
    "/v1/responses:stream",
}

_BLOCKED_SUFFIXES: Tuple[str, ...] = (
    "/content",
    "/results",
)

_BLOCKED_METHOD_PATH_REGEX: Set[Tuple[str, re.Pattern[str]]] = {
    ("POST", re.compile(r"^/v1/files$")),
    ("POST", re.compile(r"^/v1/images/(edits|variations)$")),
    ("POST", re.compile(r"^/v1/videos$")),  # create video is multipart/form-data
}

# Allowlist: (methods, regex)
_ALLOWLIST: Tuple[Tuple[Set[str], re.Pattern[str]], ...] = (
    # ---- Responses (JSON) ----
    ({"POST"}, re.compile(r"^/v1/responses$")),
    ({"POST"}, re.compile(r"^/v1/responses/compact$")),
    ({"GET"}, re.compile(r"^/v1/responses/[A-Za-z0-9_-]+$")),
    ({"DELETE"}, re.compile(r"^/v1/responses/[A-Za-z0-9_-]+$")),
    ({"POST"}, re.compile(r"^/v1/responses/[A-Za-z0-9_-]+/cancel$")),
    ({"GET"}, re.compile(r"^/v1/responses/[A-Za-z0-9_-]+/input_items$")),
    ({"POST"}, re.compile(r"^/v1/responses/input_tokens$")),

    # ---- Embeddings (JSON) ----
    ({"POST"}, re.compile(r"^/v1/embeddings$")),

    # ---- Models (JSON) ----
    ({"GET"}, re.compile(r"^/v1/models$")),
    ({"GET"}, re.compile(r"^/v1/models/[^/]+$")),

    # ---- Images (JSON only: generations) ----
    ({"POST"}, re.compile(r"^/v1/images/generations$")),
    ({"POST"}, re.compile(r"^/v1/images$")),

    # ---- Videos (metadata only via proxy; content is binary, create is multipart) ----
    ({"GET"}, re.compile(r"^/v1/videos$")),
    ({"GET"}, re.compile(r"^/v1/videos/[^/]+$")),
    ({"DELETE"}, re.compile(r"^/v1/videos/[^/]+$")),

    # ---- Vector Stores (JSON) ----
    ({"GET"}, re.compile(r"^/v1/vector_stores$")),
    ({"POST"}, re.compile(r"^/v1/vector_stores$")),
    ({"GET"}, re.compile(r"^/v1/vector_stores/[^/]+$")),
    ({"POST"}, re.compile(r"^/v1/vector_stores/[^/]+$")),
    ({"DELETE"}, re.compile(r"^/v1/vector_stores/[^/]+$")),
    ({"POST"}, re.compile(r"^/v1/vector_stores/[^/]+/search$")),
    ({"PUT"}, re.compile(r"^/v1/vector_stores/[^/]+$")),
    ({"PATCH"}, re.compile(r"^/v1/vector_stores/[^/]+$")),
    
    # vector store files
    ({"POST"}, re.compile(r"^/v1/vector_stores/[^/]+/files$")),
    ({"GET"}, re.compile(r"^/v1/vector_stores/[^/]+/files$")),
    ({"GET"}, re.compile(r"^/v1/vector_stores/[^/]+/files/[^/]+$")),
    ({"POST"}, re.compile(r"^/v1/vector_stores/[^/]+/files/[^/]+$")),
    ({"DELETE"}, re.compile(r"^/v1/vector_stores/[^/]+/files/[^/]+$")),

    # vector store file batches
    ({"POST"}, re.compile(r"^/v1/vector_stores/[^/]+/file_batches$")),
    ({"GET"}, re.compile(r"^/v1/vector_stores/[^/]+/file_batches/[^/]+$")),
    ({"POST"}, re.compile(r"^/v1/vector_stores/[^/]+/file_batches/[^/]+/cancel$")),
    ({"GET"}, re.compile(r"^/v1/vector_stores/[^/]+/file_batches/[^/]+/files$")),

    # ---- Containers (JSON control plane only) ----
    ({"GET"}, re.compile(r"^/v1/containers$")),
    ({"POST"}, re.compile(r"^/v1/containers$")),
    ({"GET"}, re.compile(r"^/v1/containers/[^/]+$")),
    ({"DELETE"}, re.compile(r"^/v1/containers/[^/]+$")),

    # ---- Conversations (JSON) ----
    ({"POST"}, re.compile(r"^/v1/conversations$")),
    ({"GET"}, re.compile(r"^/v1/conversations$")),
    ({"GET"}, re.compile(r"^/v1/conversations/[^/]+$")),
    ({"POST"}, re.compile(r"^/v1/conversations/[^/]+$")),
    ({"DELETE"}, re.compile(r"^/v1/conversations/[^/]+$")),

    # ---- Files (JSON metadata only; content is binary; create is multipart) ----
    ({"GET"}, re.compile(r"^/v1/files$")),
    ({"GET"}, re.compile(r"^/v1/files/[A-Za-z0-9_-]+$")),
    ({"DELETE"}, re.compile(r"^/v1/files/[A-Za-z0-9_-]+$")),

    # ---- Batches (JSON) ----
    ({"GET"}, re.compile(r"^/v1/batches$")),
    ({"POST"}, re.compile(r"^/v1/batches$")),
    ({"GET"}, re.compile(r"^/v1/batches/[^/]+$")),
    ({"POST"}, re.compile(r"^/v1/batches/[^/]+/cancel$")),
)


def _normalize_path(path: str) -> str:
    p = (path or "").strip()
    if not p:
        raise HTTPException(status_code=400, detail="path is required")

    if "://" in p or p.lower().startswith("http"):
        raise HTTPException(status_code=400, detail="path must be an OpenAI API path, not a URL")

    if "?" in p:
        raise HTTPException(status_code=400, detail="path must not include '?'; use `query` field")

    if not p.startswith("/"):
        p = "/" + p

    if p.startswith("/v1"):
        normalized = p
    elif p.startswith("v1/"):
        normalized = "/" + p
    else:
        normalized = "/v1" + p

    while "//" in normalized:
        normalized = normalized.replace("//", "/")

    return normalized


def _blocked_reason(method: str, path: str, body: Any) -> Optional[str]:
    if isinstance(body, dict) and body.get("stream") is True:
        return "stream=true is not allowed via /v1/proxy (use explicit streaming route)"

    if ":" in path:
        return "':' paths are not allowed via /v1/proxy"

    if ".." in path or "#" in path:
        return "path contains illegal sequences"
    if any(ch.isspace() for ch in path):
        return "path must not contain whitespace"

    if path in _BLOCKED_PATHS:
        return "path is blocked"

    for prefix in _BLOCKED_PREFIXES:
        if path.startswith(prefix):
            return f"blocked prefix: {prefix}"

    for suffix in _BLOCKED_SUFFIXES:
        if path.endswith(suffix):
            return f"blocked suffix: {suffix}"

    for (m, rx) in _BLOCKED_METHOD_PATH_REGEX:
        if method == m and rx.match(path):
            return "multipart endpoint blocked via /v1/proxy"

    return None


def _is_allowlisted(method: str, path: str) -> bool:
    for methods, rx in _ALLOWLIST:
        if method in methods and rx.match(path):
            return True
    return False


@router.post("/proxy")
async def proxy(call: ProxyRequest, request: Request) -> Response:
    method = (call.method or "").strip().upper()
    if method not in _ALLOWED_METHODS:
        raise HTTPException(status_code=400, detail=f"Unsupported method: {call.method}")

    path = _normalize_path(call.path)

    reason = _blocked_reason(method, path, call.body)
    if reason:
        raise HTTPException(status_code=403, detail={"error": reason})

    if not _is_allowlisted(method, path):
        raise HTTPException(status_code=403, detail="method/path not allowlisted for /v1/proxy")

    return await forward_openai_method_path(
        method=method,
        path=path,
        query=call.query,
        json_body=call.body,
        inbound_headers=request.headers,
    )
