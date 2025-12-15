from __future__ import annotations

import re
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import AliasChoices, BaseModel, Field

from app.api.forward_openai import forward_openai_method_path

router = APIRouter(prefix="/v1", tags=["proxy"])


class ProxyRequest(BaseModel):
    """
    Action-friendly proxy envelope.

    Compatibility notes:
      - Accepts either `body` or `json` for the outbound JSON payload.
      - Accepts either `query` or `params` for outbound query parameters.

    Example:
      {
        "method": "POST",
        "path": "/v1/embeddings",
        "json": {"model": "...", "input": "ping"}
      }
    """

    method: str = Field(..., description="HTTP method", examples=["GET", "POST"])
    path: str = Field(..., description="Upstream path (should start with /v1/...)")

    # Accept both keys: "query" and "params"
    query: Optional[Dict[str, Any]] = Field(
        default=None,
        validation_alias=AliasChoices("query", "params"),
        description="Optional query parameters.",
        examples=[{"limit": 10}],
    )

    # Accept both keys: "body" and "json"
    body: Optional[Any] = Field(
        default=None,
        validation_alias=AliasChoices("body", "json"),
        description="Optional JSON body for POST/PATCH requests.",
        examples=[{"model": "gpt-4.1-mini", "input": "hello"}],
    )


# -------------------------------------------------------------------
# Allowlist policy (ONLY allow safe/needed OpenAI endpoints via /v1/proxy)
# -------------------------------------------------------------------

_ALLOWLIST: list[tuple[str, re.Pattern[str]]] = [
    # Responses (JSON only). Streaming is blocked separately.
    ("POST", re.compile(r"^/v1/responses$")),
    ("GET", re.compile(r"^/v1/responses/[^/]+$")),
    ("DELETE", re.compile(r"^/v1/responses/[^/]+$")),
    ("POST", re.compile(r"^/v1/responses/[^/]+/cancel$")),
    ("GET", re.compile(r"^/v1/responses/[^/]+/input_items$")),
    ("POST", re.compile(r"^/v1/responses/input_tokens$")),
    ("POST", re.compile(r"^/v1/responses/input_tokens/estimate$")),
    # Embeddings
    ("POST", re.compile(r"^/v1/embeddings$")),
    # Models
    ("GET", re.compile(r"^/v1/models$")),
    ("GET", re.compile(r"^/v1/models/[^/]+$")),
    # Vector stores (everything under /v1/vector_stores/*)
    ("GET", re.compile(r"^/v1/vector_stores$")),
    ("POST", re.compile(r"^/v1/vector_stores$")),
    ("GET", re.compile(r"^/v1/vector_stores/.*$")),
    ("POST", re.compile(r"^/v1/vector_stores/.*$")),
    ("DELETE", re.compile(r"^/v1/vector_stores/.*$")),
    # Conversations
    ("GET", re.compile(r"^/v1/conversations$")),
    ("POST", re.compile(r"^/v1/conversations$")),
    ("GET", re.compile(r"^/v1/conversations/.*$")),
    ("POST", re.compile(r"^/v1/conversations/.*$")),
    ("DELETE", re.compile(r"^/v1/conversations/.*$")),
    ("PATCH", re.compile(r"^/v1/conversations/.*$")),
    # Containers
    ("GET", re.compile(r"^/v1/containers$")),
    ("POST", re.compile(r"^/v1/containers$")),
    ("GET", re.compile(r"^/v1/containers/.*$")),
    ("POST", re.compile(r"^/v1/containers/.*$")),
    ("DELETE", re.compile(r"^/v1/containers/.*$")),
    # Batches
    ("POST", re.compile(r"^/v1/batches$")),
    ("GET", re.compile(r"^/v1/batches$")),
    ("GET", re.compile(r"^/v1/batches/[^/]+$")),
    ("POST", re.compile(r"^/v1/batches/[^/]+/cancel$")),
    # Images (JSON-only)
    ("POST", re.compile(r"^/v1/images/generations$")),
    ("POST", re.compile(r"^/v1/images$")),
    # Videos (JSON control plane). Content download is binary and should use explicit route.
    ("POST", re.compile(r"^/v1/videos/generations$")),
    ("GET", re.compile(r"^/v1/videos$")),
    ("GET", re.compile(r"^/v1/videos/[^/]+$")),
    ("DELETE", re.compile(r"^/v1/videos/[^/]+$")),
    # Uploads (control plane). Multipart parts are blocked separately.
    ("POST", re.compile(r"^/v1/uploads$")),
    ("POST", re.compile(r"^/v1/uploads/[^/]+/complete$")),
    ("POST", re.compile(r"^/v1/uploads/[^/]+/cancel$")),
]

# Local-only endpoints that should never be proxied upstream via /v1/proxy
_BLOCKED_LOCAL_PATHS = {
    "/v1/health",
    "/v1/manifest",
    "/v1/actions/ping",
    "/v1/actions/relay_info",
    "/v1/proxy",
    # Relay convenience endpoints (not OpenAI upstream endpoints)
    "/v1/responses/compact",
}

# Explicitly blocked prefixes (even if allowlisted elsewhere)
_BLOCKED_PREFIXES = (
    "/v1/admin",
    "/v1/dashboard",
    "/v1/webhooks",
    "/v1/assistants",  # higher-risk surface; keep explicit if ever added
    "/v1/audio",  # keep explicit if you later decide to proxy it
    "/v1/realtime",  # websocket/event surfaces are not Actions-friendly
)

# Multipart / binary endpoints we intentionally do NOT support through /v1/proxy
_BLOCKED_PATH_PATTERNS = [
    re.compile(r"^/v1/files(/|$)"),  # files upload is multipart
    re.compile(r"^/v1/images/edits$"),  # multipart
    re.compile(r"^/v1/images/variations$"),  # multipart
    re.compile(r"^/v1/uploads/[^/]+/parts$"),  # multipart
    re.compile(r"^/v1/videos/[^/]+/content$"),  # binary stream
]


def _blocked_reason(method: str, path: str, body: Any) -> Optional[str]:
    if path in _BLOCKED_LOCAL_PATHS:
        return "local endpoint is not proxyable"

    for prefix in _BLOCKED_PREFIXES:
        if path.startswith(prefix):
            return f"blocked prefix: {prefix}"

    for pat in _BLOCKED_PATH_PATTERNS:
        if pat.match(path):
            return "multipart/binary endpoint must use explicit route, not /v1/proxy"

    # Block streaming through /v1/proxy (Actions-unfriendly)
    if path == "/v1/responses:stream":
        return "streaming endpoints are not supported via /v1/proxy"
    if isinstance(body, dict) and body.get("stream") is True:
        return "stream=true requests are not supported via /v1/proxy"

    return None


def _is_allowlisted(method: str, path: str) -> bool:
    for m, rx in _ALLOWLIST:
        if method == m and rx.match(path):
            return True
    return False


@router.post("/proxy")
async def proxy(request: Request, call: ProxyRequest) -> Response:
    """
    POST /v1/proxy
    A constrained proxy to OpenAI endpoints. Only allowlisted paths are forwarded.

    The incoming request headers (Authorization/Beta/etc.) are forwarded upstream by
    forward_openai_method_path.

    NOTE: This endpoint enforces allowlisting. Unknown method/path returns 403.
    """
    method = call.method.upper().strip()
    path = call.path.strip()

    # Normalize path: allow clients to pass "vector_stores/..." etc.
    if not path.startswith("/"):
        path = "/" + path
    if not path.startswith("/v1/"):
        # If they provided "/models" assume they mean "/v1/models"
        if path.startswith("/v1"):
            # e.g. "/v1models" -> fix
            path = "/v1/" + path[len("/v1") :].lstrip("/")
        else:
            path = "/v1/" + path.lstrip("/")

    reason = _blocked_reason(method, path, call.body)
    if reason:
        raise HTTPException(status_code=403, detail={"error": reason})

    if not _is_allowlisted(method, path):
        raise HTTPException(
            status_code=403,
            detail={"error": "method/path not allowlisted for /v1/proxy"},
        )

    return await forward_openai_method_path(
        request=request,
        method=method,
        path=path,
        query=call.query,
        json_body=call.body,
    )
