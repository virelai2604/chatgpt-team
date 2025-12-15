from __future__ import annotations

import re
from typing import Any, Dict, Optional, Sequence, Tuple

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import AliasChoices, BaseModel, ConfigDict, Field, model_validator

from app.api.forward_openai import forward_openai_method_path

router = APIRouter(prefix="/v1", tags=["proxy"])


class ProxyRequest(BaseModel):
    """
    Action-friendly proxy envelope (JSON-only).

    This endpoint is intentionally NOT a generic open proxy. It only forwards
    allowlisted (method, path) pairs and assumes a JSON body when applicable.

    Non-JSON routes (multipart uploads, binary downloads, SSE/WebSocket) should be
    implemented as explicit relay routes/wrappers.

    Compatibility:
      - `body` may also be provided as `json` or `json_body`
      - `query` may also be provided as `params`
    """

    # Prevent silent typos (e.g., sending "jon" instead of "json") that can cause
    # confusing upstream errors.
    model_config = ConfigDict(extra="forbid")

    method: str = Field(..., description="HTTP method: GET, POST, PUT, PATCH, DELETE")
    path: str = Field(..., description="Upstream OpenAI path, e.g. /v1/responses or /responses")

    query: Optional[Dict[str, Any]] = Field(
        default=None,
        validation_alias=AliasChoices("query", "params"),
        description="Query parameters (dict/object). Accepts 'query' or 'params'.",
    )

    body: Optional[Any] = Field(
        default=None,
        validation_alias=AliasChoices("body", "json", "json_body"),
        description="JSON body for POST/PUT/PATCH. Accepts 'body', 'json', or 'json_body'.",
    )

    @model_validator(mode="after")
    def _avoid_empty_json_body_parse_errors(self) -> "ProxyRequest":
        """
        If a caller sends Content-Type: application/json but omits the body (or uses
        a wrong field name), OpenAI commonly replies with a JSON parse error.

        Defaulting to {} for JSON methods yields a clearer upstream validation error
        instead (e.g., missing required fields), and prevents accidental empty-body
        parse errors.
        """
        m = (self.method or "").strip().upper()
        if self.body is None and m in {"POST", "PUT", "PATCH"}:
            self.body = {}
        return self


_ALLOWED_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE"}

# Relay-local endpoints (never forward to upstream)
_BLOCKED_LOCAL_PATHS = {
    "/v1/health",
    "/v1/ready",
    "/v1/version",
    "/v1/manifest",
    "/v1/tools",
    "/v1/tools/manifest",
    "/v1/proxy",
    "/v1/responses:stream",  # relay/streaming helper; not JSON-friendly via Actions
}

# Whole families that are not JSON-friendly for a simple proxy
_BLOCKED_PREFIXES = (
    "/v1/audio",     # multipart / binary
    "/v1/realtime",  # websocket/webrtc flows (even if some session endpoints are HTTP)
)

# Any path ending with /content returns bytes (binary download)
_BLOCKED_SUFFIXES = ("/content",)

# Known multipart-only endpoints or patterns that should not be used via this JSON proxy
_BLOCKED_MULTIPART_REGEXES = (
    re.compile(r"^/v1/files$"),                   # POST upload is multipart
    re.compile(r"^/v1/uploads/[^/]+/parts$"),     # upload parts is multipart
    re.compile(r"^/v1/images/edits$"),            # typically multipart
    re.compile(r"^/v1/images/variations$"),       # multipart
    re.compile(r"^/v1/containers/[^/]+/files$"),  # POST is multipart (GET is OK; handled by allowlist)
)

# Allowlist of upstream targets for the JSON-only proxy.
# Keep this conservative: add routes deliberately, with tests.
_ALLOWLIST: Sequence[Tuple[set[str], re.Pattern[str]]] = (
    # --- Responses (JSON) ---
    ({"POST"}, re.compile(r"^/v1/responses$")),
    ({"POST"}, re.compile(r"^/v1/responses/compact$")),
    ({"POST"}, re.compile(r"^/v1/responses/input_tokens$")),
    ({"GET", "DELETE"}, re.compile(r"^/v1/responses/[^/]+$")),
    ({"POST"}, re.compile(r"^/v1/responses/[^/]+/cancel$")),
    ({"GET"}, re.compile(r"^/v1/responses/[^/]+/input_items$")),

    # --- Embeddings / Models (JSON) ---
    ({"POST"}, re.compile(r"^/v1/embeddings$")),
    ({"GET"}, re.compile(r"^/v1/models$")),
    ({"GET"}, re.compile(r"^/v1/models/[^/]+$")),

    # --- Batches (JSON) ---
    ({"GET", "POST"}, re.compile(r"^/v1/batches$")),
    ({"GET"}, re.compile(r"^/v1/batches/[^/]+$")),
    ({"POST"}, re.compile(r"^/v1/batches/[^/]+/cancel$")),

    # --- Vector Stores (JSON; broad but still constrained to /v1/vector_stores/*) ---
    ({"GET", "POST", "DELETE"}, re.compile(r"^/v1/vector_stores(?:/.*)?$")),

    # --- Conversations (JSON; constrained to /v1/conversations/*) ---
    ({"GET", "POST", "DELETE"}, re.compile(r"^/v1/conversations(?:/.*)?$")),

    # --- Containers (JSON) ---
    ({"GET", "POST"}, re.compile(r"^/v1/containers$")),
    ({"GET", "DELETE"}, re.compile(r"^/v1/containers/[^/]+$")),

    # Container files: allow metadata routes only (POST upload is blocked via multipart rule above)
    ({"GET"}, re.compile(r"^/v1/containers/[^/]+/files$")),
    ({"GET", "DELETE"}, re.compile(r"^/v1/containers/[^/]+/files/[^/]+$")),

    # --- Uploads (JSON for create/complete/cancel; parts are multipart and blocked) ---
    ({"POST"}, re.compile(r"^/v1/uploads$")),
    ({"POST"}, re.compile(r"^/v1/uploads/[^/]+/complete$")),
    ({"POST"}, re.compile(r"^/v1/uploads/[^/]+/cancel$")),

    # --- Files (JSON metadata only; upload is multipart and blocked; /content is binary blocked) ---
    ({"GET"}, re.compile(r"^/v1/files$")),
    ({"GET", "DELETE"}, re.compile(r"^/v1/files/[^/]+$")),

    # --- Images (JSON generation only; edits/variations blocked as multipart) ---
    ({"POST"}, re.compile(r"^/v1/images/generations$")),

    # --- Videos (JSON create/list/retrieve/delete/remix; /content is binary blocked) ---
    ({"GET", "POST"}, re.compile(r"^/v1/videos$")),
    ({"GET", "DELETE"}, re.compile(r"^/v1/videos/[^/]+$")),
    ({"POST"}, re.compile(r"^/v1/videos/[^/]+/remix$")),
)


def _normalize_path(path: str) -> str:
    p = (path or "").strip()
    if not p.startswith("/"):
        p = "/" + p

    # Defensive checks: block absolute URLs and traversal-ish inputs
    if "://" in p or p.startswith("/http") or ".." in p or "\\" in p:
        raise HTTPException(status_code=400, detail="invalid path")

    # Force /v1 prefix (so callers can pass /responses or /v1/responses)
    if not p.startswith("/v1"):
        p = "/v1" + p

    return p


def _blocked_reason(method: str, path: str) -> Optional[str]:
    if path in _BLOCKED_LOCAL_PATHS:
        return "path is relay-local; not proxyable via /v1/proxy"

    for prefix in _BLOCKED_PREFIXES:
        if path.startswith(prefix):
            return f"path family not supported via JSON proxy: {prefix}"

    for suffix in _BLOCKED_SUFFIXES:
        if path.endswith(suffix):
            return "binary /content downloads are not supported via /v1/proxy"

    # Multipart blocks:
    for rx in _BLOCKED_MULTIPART_REGEXES:
        if rx.match(path):
            # Special case: allow GET on container files list, block POST upload
            if rx.pattern == r"^/v1/containers/[^/]+/files$" and method == "GET":
                return None
            return "multipart/form-data route not supported via JSON proxy"

    return None


def _is_allowlisted(method: str, path: str) -> bool:
    for methods, pattern in _ALLOWLIST:
        if method in methods and pattern.match(path):
            return True
    return False


@router.post("/proxy", response_class=Response)
async def proxy(call: ProxyRequest, request: Request) -> Response:
    method = (call.method or "").upper().strip()
    if method not in _ALLOWED_METHODS:
        raise HTTPException(status_code=400, detail="unsupported method")

    path = _normalize_path(call.path)

    reason = _blocked_reason(method, path)
    if reason:
        raise HTTPException(status_code=403, detail=reason)

    if not _is_allowlisted(method, path):
        raise HTTPException(status_code=403, detail="method/path not allowlisted for /v1/proxy")

    return await forward_openai_method_path(
        method=method,
        path=path,
        query=call.query,
        json_body=call.body,
        inbound_headers=request.headers,
    )
