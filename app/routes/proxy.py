from __future__ import annotations

import re
from typing import Any, Dict, Optional, Set, Tuple

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import AliasChoices, BaseModel, ConfigDict, Field, model_validator

from app.api.forward_openai import forward_openai_method_path

router = APIRouter(prefix="/v1", tags=["proxy"])


class ProxyRequest(BaseModel):
    """
    Action-friendly proxy envelope (Option A).

    NOTE:
    - We intentionally do NOT use a field named `json`, because it shadows
      BaseModel.json() and triggers Pydantic warnings.
    - For backward compatibility, we still ACCEPT an input key named "json"
      as an alias to `body`.
    """

    model_config = ConfigDict(extra="forbid")

    method: str = Field(..., description="HTTP method: GET, POST, PUT, PATCH, DELETE")
    path: str = Field(..., description="Upstream OpenAI path, e.g. /v1/responses")

    # Accept multiple common spellings (client convenience).
    query: Optional[Dict[str, Any]] = Field(
        default=None,
        validation_alias=AliasChoices("query", "params", "query_params"),
        description="Query parameters (object/dict)",
    )

    # Back-compat: accept {"json": {...}} from older clients/examples
    body: Optional[Any] = Field(
        default=None,
        validation_alias=AliasChoices("body", "json", "json_body"),
        description="JSON body for POST/PUT/PATCH requests",
    )

    @model_validator(mode="after")
    def _avoid_empty_json_body_parse_errors(self) -> "ProxyRequest":
        """
        Guardrail: Some clients send body=null or body="" inconsistently.
        Keep it as None unless it's a real JSON object/array/etc.
        """
        if self.body == "":
            self.body = None
        return self


_ALLOWED_METHODS: Set[str] = {"GET", "POST", "PUT", "PATCH", "DELETE"}

# Hard block sensitive local paths from ever being proxied upstream.
_BLOCKED_PATHS: Set[str] = {
    "/",
    "/health",
    "/openapi.json",
    "/docs",
    "/redoc",
    "/manifest",
    "/v1/manifest",
    "/actions/ping",
    "/v1/actions/ping",
    "/actions/relay_info",
    "/v1/actions/relay_info",
    "/v1/proxy",  # prevent recursion
    "/v1/admin",
}

# Block prefixes/suffixes that are either local-only or unsafe via proxy envelope.
_BLOCKED_PREFIXES: Tuple[str, ...] = (
    "/v1/audio",  # often multipart/binary; prefer explicit routes
    "/v1/realtime",  # special protocol
)
_BLOCKED_SUFFIXES: Tuple[str, ...] = (
    "/content",
    "/results",
)

# Multipart endpoints that should not be routed via JSON envelope
_BLOCKED_METHOD_PATH_REGEX: Set[Tuple[str, re.Pattern[str]]] = {
    ("POST", re.compile(r"^/v1/files$")),
    ("POST", re.compile(r"^/v1/images/(edits|variations)$")),
    ("POST", re.compile(r"^/v1/videos$")),  # per API ref, create video is multipart/form-data
}

# Allowlist: (methods, regex)
_ALLOWLIST: Tuple[Tuple[Set[str], re.Pattern[str]], ...] = (
    # ---- Responses (JSON) ----
    ({"POST"}, re.compile(r"^/v1/responses$")),
    ({"GET", "DELETE"}, re.compile(r"^/v1/responses/[^/]+$")),
    ({"POST"}, re.compile(r"^/v1/responses/[^/]+/cancel$")),
    ({"GET"}, re.compile(r"^/v1/responses/[^/]+/input_items$")),
    ({"POST"}, re.compile(r"^/v1/responses/input_tokens$")),
    # ---- Embeddings ----
    ({"POST"}, re.compile(r"^/v1/embeddings$")),
    # ---- Images (generations only; edits are multipart and blocked) ----
    ({"POST"}, re.compile(r"^/v1/images$")),
    ({"POST"}, re.compile(r"^/v1/images/generations$")),
    # ---- Models ----
    ({"GET"}, re.compile(r"^/v1/models$")),
    ({"GET"}, re.compile(r"^/v1/models/[^/]+$")),
    # ---- Vector stores (catch-all under /v1/vector_stores/*) ----
    ({"GET", "POST", "PUT", "PATCH", "DELETE"}, re.compile(r"^/v1/vector_stores$")),
    ({"GET", "POST", "PUT", "PATCH", "DELETE"}, re.compile(r"^/v1/vector_stores/.*$")),
    # ---- Uploads (JSON endpoints; parts upload is multipart and handled explicitly elsewhere) ----
    ({"POST"}, re.compile(r"^/v1/uploads$")),
    ({"POST"}, re.compile(r"^/v1/uploads/[^/]+/(complete|cancel)$")),
    # ---- Batches ----
    ({"GET", "POST"}, re.compile(r"^/v1/batches$")),
    ({"GET"}, re.compile(r"^/v1/batches/[^/]+$")),
    ({"POST"}, re.compile(r"^/v1/batches/[^/]+/cancel$")),
    # ---- Containers (JSON metadata endpoints) ----
    ({"GET", "POST"}, re.compile(r"^/v1/containers$")),
    ({"GET", "POST", "PUT", "PATCH", "DELETE"}, re.compile(r"^/v1/containers/.*$")),
    # ---- Conversations (JSON) ----
    ({"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}, re.compile(r"^/v1/conversations$")),
    ({"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}, re.compile(r"^/v1/conversations/.*$")),
    # ---- Videos (JSON endpoints; POST /v1/videos is multipart and blocked above) ----
    ({"GET"}, re.compile(r"^/v1/videos$")),
    ({"GET"}, re.compile(r"^/v1/videos/[^/]+$")),
    ({"DELETE"}, re.compile(r"^/v1/videos/[^/]+$")),
    ({"POST"}, re.compile(r"^/v1/videos/[^/]+/remix$")),
)


def _normalize_path(path: str) -> str:
    p = (path or "").strip()

    if not p:
        raise HTTPException(status_code=400, detail="path is required")

    # Disallow full URLs; only allow API paths.
    if "://" in p or p.lower().startswith("http"):
        raise HTTPException(status_code=400, detail="path must be an OpenAI API path, not a URL")

    # Disallow embedded query strings (use `query` field).
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

    # Collapse accidental double slashes
    while "//" in normalized:
        normalized = normalized.replace("//", "/")

    return normalized


def _blocked_reason(method: str, path: str, body: Any) -> Optional[str]:
    # No streaming via proxy envelope
    if isinstance(body, dict) and body.get("stream") is True:
        return "stream=true is not allowed via /v1/proxy (use explicit streaming route)"

    # Block weird colon paths like /v1/responses:stream
    if ":" in path:
        return "':' paths are not allowed via /v1/proxy"

    # Basic traversal guards
    if ".." in path or "#" in path:
        return "path contains illegal sequences"
    if any(ch.isspace() for ch in path):
        return "path must not contain whitespace"

    if path in _BLOCKED_PATHS:
        return "Path blocked by policy"

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
        # IMPORTANT: our global HTTPException handler does `str(exc.detail)`,
        # so keep this as a string (not a dict) for clean error messages.
        raise HTTPException(status_code=403, detail=reason)

    if not _is_allowlisted(method, path):
        raise HTTPException(status_code=403, detail="method/path not allowlisted for /v1/proxy")

    # IMPORTANT FIX:
    # forward_openai_method_path() expects inbound_headers (not request=request).
    return await forward_openai_method_path(
        method=method,
        path=path,
        query=call.query,
        json_body=call.body,
        inbound_headers=request.headers,
    )
