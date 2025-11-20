from __future__ import annotations

import os
from typing import Any, Dict, Optional

import httpx
from fastapi import HTTPException, Request, Response

from app.utils.logger import get_logger

logger = get_logger("relay.forwarder")

# Default timeout in seconds; mirrors RELAY_TIMEOUT env if present.
DEFAULT_TIMEOUT = float(os.getenv("RELAY_TIMEOUT", "120"))


def _get_openai_base() -> str:
    """
    Return the upstream OpenAI-compatible base URL, without a trailing slash.

    pytest.ini sets:
      OPENAI_API_BASE=https://api.openai.com
    and expects us to append `/v1` ourselves.
    """
    base = os.getenv("OPENAI_API_BASE", "https://api.openai.com").rstrip("/")
    return base


def _normalize_upstream_path(request: Request, upstream_path: Optional[str]) -> str:
    """
    Ensure we end up with a path like `/responses`, `/embeddings`, `/files/{id}`.

    - If caller passes upstream_path explicitly, use that.
    - Otherwise derive from request.url.path and strip the `/v1` prefix,
      because our base URL does not include `/v1`.
    """
    if upstream_path is not None:
        path = upstream_path
    else:
        path = request.url.path or "/"
        # Strip leading /v1 from local paths, e.g. "/v1/embeddings" -> "/embeddings"
        if path.startswith("/v1"):
            path = path[len("/v1") :]
            if not path:
                path = "/"

    if not path.startswith("/"):
        path = "/" + path

    return path


def _build_upstream_headers(request: Request) -> Dict[str, str]:
    """
    Build a clean set of headers for the upstream OpenAI API.

    Rules:
    - Always enforce Authorization from OPENAI_API_KEY (never trust client).
    - Forward a safe subset of client headers:
        * content-type, accept
        * openai-* headers EXCEPT openai-organization
        * x-request-id
    - Do NOT set OpenAI-Organization at all (we assume project keys).
    """
    upstream_headers: Dict[str, str] = {}

    # 1) Forward a minimal, safe subset of client headers.
    for name, value in request.headers.items():
        lname = name.lower()

        # Basic content negotiation headers
        if lname in ("content-type", "accept"):
            upstream_headers[name] = value

        # Forward OpenAI feature / beta flags, but never organization.
        elif lname.startswith("openai-"):
            if lname != "openai-organization":
                upstream_headers[name] = value

        # Preserve client request-id for tracing if present.
        elif lname == "x-request-id":
            upstream_headers[name] = value

    # 2) Enforce API key from environment (mandatory).
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        # If the relay is misconfigured, fail fast and clearly.
        raise HTTPException(
            status_code=500,
            detail="Relay misconfiguration: OPENAI_API_KEY is not set.",
        )

    upstream_headers["Authorization"] = f"Bearer {api_key}"

    # 3) Remove hop-by-hop and length/encoding headers if they slipped through.
    for h in ("host", "content-length", "connection"):
        upstream_headers.pop(h, None)

    return upstream_headers


async def forward_openai_request(
    request: Request,
    upstream_path: Optional[str] = None,
    method: Optional[str] = None,
    *,
    timeout: Optional[float] = None,
    stream: Optional[bool] = None,
    **_: Any,
) -> Response:
    """
    Generic relay to the upstream OpenAI-compatible API.

    This is intentionally forgiving for the callers used in your tests:

    - If `upstream_path` is not provided, we infer it from `request.url.path`
      and strip the `/v1` prefix.
    - If `method` is not provided, we infer it from `request.method`.
    - Extra keyword args are accepted and ignored (to stay compatible with
      any middleware/orchestrator that passes extra flags).

    The tests rely on:
      - correct rewriting from local `/v1/...` to upstream `/v1/...`
      - correct forwarding of JSON and multipart bodies
      - returning the upstream status code and body.
    """
    base = _get_openai_base()

    # Method from caller or incoming request
    method = (method or request.method).upper()

    # Path: either explicit or derived from the request
    normalized_path = _normalize_upstream_path(request, upstream_path)
    url = f"{base}/v1{normalized_path}"

    # Query parameters
    params: Dict[str, str] = dict(request.query_params)

    # Raw body – works for JSON, multipart/form-data, and binary
    body: bytes = await request.body()

    # Build upstream headers with our policy.
    upstream_headers = _build_upstream_headers(request)
    request_id = upstream_headers.get("x-request-id")

    logger.debug(
        {
            "event": "forward_openai_request.start",
            "method": method,
            "url": url,
            "params": params,
            "request_id": request_id,
        }
    )

    try:
        async with httpx.AsyncClient(timeout=timeout or DEFAULT_TIMEOUT) as client:
            upstream_response = await client.request(
                method=method,
                url=url,
                params=params,
                # For GET/DELETE, content=None is fine; httpx ignores it.
                content=body if body else None,
                headers=upstream_headers,
            )
    except httpx.RequestError as exc:
        logger.error(
            {
                "event": "openai_upstream_error",
                "error": str(exc),
                "url": str(getattr(getattr(exc, "request", None), "url", url)),
            }
        )
        raise HTTPException(
            status_code=502,
            detail="Upstream OpenAI API request failed",
        )

    # Copy headers back, minus hop-by-hop and encoding/length that httpx has already handled.
    resp_headers: Dict[str, str] = dict(upstream_response.headers)
    for h in (
        "connection",
        "keep-alive",
        "proxy-authenticate",
        "proxy-authorization",
        "te",
        "trailers",
        "transfer-encoding",
        "upgrade",
        "content-encoding",  # avoid double-decompression in client
        "content-length",    # length no longer matches decompressed body
    ):
        resp_headers.pop(h, None)

    logger.debug(
        {
            "event": "forward_openai_request.complete",
            "status_code": upstream_response.status_code,
            "request_id": request_id,
        }
    )

    return Response(
        content=upstream_response.content,
        status_code=upstream_response.status_code,
        headers=resp_headers,
        media_type=resp_headers.get("content-type"),
    )
