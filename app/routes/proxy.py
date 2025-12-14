from __future__ import annotations

import re
from typing import Any, Dict, Optional, Sequence, Tuple

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, Field

from app.api.forward_openai import forward_openai_method_path

router = APIRouter(prefix="/v1", tags=["proxy"])


class ProxyRequest(BaseModel):
    """
    Action-friendly proxy envelope (JSON-only).

    This endpoint is intentionally constrained:
      - Good for JSON-in/JSON-out OpenAI routes
      - NOT suitable for:
          * SSE streaming
          * WebSockets (Realtime)
          * multipart/form-data uploads
          * binary /content downloads
    Those should be implemented as explicit relay routes/wrappers.
    """

    method: str = Field(..., description="HTTP method: GET, POST, PUT, PATCH, DELETE")
    path: str = Field(..., description="Upstream OpenAI path, e.g. /v1/responses")
    query: Optional[Dict[str, Any]] = Field(default=None, description="Query parameters (object/dict)")
    body: Optional[Any] = Field(default=None, description="JSON body for POST/PUT/PATCH")


_ALLOWED_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE"}

# Relay-local endpoints and helpers that must never be proxied upstream.
_BLOCKED_LOCAL_PATHS = {
    "/",
    "/health",
    "/v1/health",
    "/manifest",
    "/v1/manifest",
    "/actions/ping",
    "/actions/relay_info",
    "/v1/actions/ping",
    "/v1/actions/relay_info",
    "/v1/proxy",
    "/v1/responses/compact",   # relay convenience endpoint, not upstream
    "/v1/responses:stream",    # relay helper / SSE-ish surface
}

# Multipart / binary / websocket families (not Action-friendly).
# We block these from /v1/proxy; implement explicit routes/wrappers instead.
_BLOCKED_PREFIXES = (
    "/v1/audio",        # typically multipart/binary
)

# Regex blocks for specific multipart-heavy endpoints.
_BLOCKED_METHOD_PATH_REGEX: Sequence[Tuple[str, re.Pattern[str], str]] = [
    # OpenAI Files upload is multipart/form-data (use explicit /v1/files route or a wrapper).
    ("POST", re.compile(r"^/v1/files$"), "multipart file upload is not supported via /v1/proxy; use explicit /v1/files"),

    # Images edits/variations are multipart/form-data.
    ("POST", re.compile(r"^/v1/images/(edits|variations)$"), "multipart images endpoint is not supported via /v1/proxy"),

    # Upload parts are multipart/binary per Uploads API design.
    ("POST", re.compile(r"^/v1/uploads/[^/]+/parts$"), "upload parts (multipart/binary) not supported via /v1/proxy"),

    # Container file upload is multipart/binary.
    ("POST", re.compile(r"^/v1/containers/[^/]+/files$"), "container file upload (multipart) not supported via /v1/proxy"),
]

# Hard allowlist for "proxy everything (JSON surfaces)".
# Unknown paths are denied (403) to prevent an open proxy.
_ALLOWLIST: Sequence[Tuple[set[str], re.Pattern[str]]] = [
    # -----------------------
    # Responses (JSON)
    # -----------------------
    ({"POST"}, re.compile(r"^/v1/responses$")),
    ({"GET", "DELETE"}, re.compile(r"^/v1/responses/[^/]+$")),
    ({"POST"}, re.compile(r"^/v1/responses/[^/]+/cancel$")),
    ({"GET"}, re.compile(r"^/v1/responses/[^/]+/input_items$")),
    ({"POST"}, re.compile(r"^/v1/responses/input_tokens$")),

    # -----------------------
    # Embeddings (JSON)
    # -----------------------
    ({"POST"}, re.compile(r"^/v1/embeddings$")),

    # -----------------------
    # Models (JSON)
    # -----------------------
    ({"GET"}, re.compile(r"^/v1/models$")),
    ({"GET"}, re.compile(r"^/v1/models/[^/]+$")),

    # -----------------------
    # Images (JSON generation only)
    # -----------------------
    ({"POST"}, re.compile(r"^/v1/images/generations$")),

    # -----------------------
    # Videos (JSON control plane)
    # -----------------------
    ({"POST"}, re.compile(r"^/v1/videos/generations$")),
    ({"GET"}, re.compile(r"^/v1/videos$")),
    ({"GET", "DELETE"}, re.compile(r"^/v1/videos/[^/]+$")),

    # -----------------------
    # Files (JSON list/retrieve/delete)
    # Upload is multipart and blocked above.
    # -----------------------
    ({"GET"}, re.compile(r"^/v1/files$")),
    ({"GET", "DELETE"}, re.compile(r"^/v1/files/[^/]+$")),

    # -----------------------
    # Uploads (JSON control plane)
    # Parts are blocked above.
    # -----------------------
    ({"POST"}, re.compile(r"^/v1/uploads$")),
    ({"GET", "DELETE"}, re.compile(r"^/v1/uploads/[^/]+$")),
    ({"POST"}, re.compile(r"^/v1/uploads/[^/]+/complete$")),
    ({"POST"}, re.compile(r"^/v1/uploads/[^/]+/cancel$")),

    # -----------------------
    # Batches (JSON)
    # -----------------------
    ({"POST", "GET"}, re.compile(r"^/v1/batches$")),
    ({"GET"}, re.compile(r"^/v1/batches/[^/]+$")),
    ({"POST"}, re.compile(r"^/v1/batches/[^/]+/cancel$")),

    # -----------------------
    # Vector stores (JSON + subroutes)
    # -----------------------
    ({"GET", "POST", "PUT", "PATCH", "DELETE"}, re.compile(r"^/v1/vector_stores(?:/.*)?$")),

    # -----------------------
    # Containers (JSON control plane; multipart upload blocked above)
    # -----------------------
    ({"POST"}, re.compile(r"^/v1/containers$")),
    ({"GET", "DELETE"}, re.compile(r"^/v1/containers/[^/]+$")),
    # If you later add more JSON subroutes, allow them explicitly; do not open wildcard by default.

    # -----------------------
    # Conversations (JSON + subroutes)
    # -----------------------
    ({"GET", "POST", "PUT", "PATCH", "DELETE"}, re.compile(r"^/v1/conversations(?:/.*)?$")),

    # -----------------------
    # Realtime (token minting only; WebSocket surfaces are not Action-friendly)
    # -----------------------
    ({"POST"}, re.compile(r"^/v1/realtime/sessions$")),
]


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

    # Collapse accidental double slashes
    while "//" in normalized:
        normalized = normalized.replace("//", "/")

    return normalized


def _blocked_reason(method: str, path: str, body: Any) -> Optional[str]:
    # No streaming via proxy envelope; Actions typically cannot consume SSE.
    if isinstance(body, dict) and body.get("stream") is True:
        return "stream=true is not allowed via /v1/proxy; use explicit streaming route"

    # Block `:stream` style paths (SSE helper endpoints, etc.)
    if ":" in path:
        return "':' paths are not allowed via /v1/proxy (streaming helpers must be explicit)"

    # Traversal / weirdness guards
    if ".." in path or "#" in path:
        return "path contains illegal sequences"
    if any(ch.isspace() for ch in path):
        return "path must not contain whitespace"

    # Never proxy relay-local endpoints
    if path in _BLOCKED_LOCAL_PATHS:
        return "relay-local endpoint is not proxyable"

    # Block broad prefixes that are known multipart/binary-heavy
    for prefix in _BLOCKED_PREFIXES:
        if path.startswith(prefix):
            return "path prefix is not supported via /v1/proxy"

    # Block binary downloads by default (Action-unfriendly)
    if path.endswith("/content"):
        return "binary /content endpoints are not supported via /v1/proxy; use explicit binary streaming route"

    # Block known multipart-heavy routes
    for m, rx, msg in _BLOCKED_METHOD_PATH_REGEX:
        if method == m and rx.match(path):
            return msg

    # Block Realtime websocket-ish surfaces (anything except /v1/realtime/sessions)
    if path.startswith("/v1/realtime") and path != "/v1/realtime/sessions":
        return "realtime websocket/event surfaces are not supported via /v1/proxy; only /v1/realtime/sessions is allowed"

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
        raise HTTPException(status_code=403, detail=reason)

    if not _is_allowlisted(method, path):
        raise HTTPException(status_code=403, detail="method/path not allowlisted for /v1/proxy")

    # Forward JSON request to upstream
    return await forward_openai_method_path(
        method=method,
        path=path,
        query=call.query,
        json_body=call.body,
        inbound_headers=request.headers,
    )
