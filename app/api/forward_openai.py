# app/api/forward_openai.py

from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional
from urllib.parse import urljoin

import httpx
from fastapi import Request, Response, status

OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_ORG_ID = os.getenv("OPENAI_ORG_ID", "")


def _build_base_url() -> str:
    base = OPENAI_API_BASE.rstrip("/")
    if not base.startswith("http://") and not base.startswith("https://"):
        base = "https://" + base
    return base


async def forward_openai_request(
    request: Request,
    *,
    subpath: Optional[str] = None,
) -> Response:
    """
    Generic forwarder for OpenAI-compatible endpoints.

    - Rebuilds the target URL from OPENAI_API_BASE + request.url.path (+ subpath).
    - Copies through method, headers, and query params.
    - Handles:
        * application/json → uses httpx `json=` so tests can see forward_spy["json"].
        * multipart/form-data → uses `files=` (for file upload endpoints).
        * everything else → falls back to `content=`.
    """

    method = request.method.upper()
    base_url = _build_base_url()

    # Build upstream path
    incoming_path = request.url.path
    if subpath:
        if not incoming_path.endswith("/"):
            incoming_path += "/"
        incoming_path += subpath

    target_url = urljoin(base_url + "/", incoming_path.lstrip("/"))

    # Query params (e.g. ?limit=, ?cursor=)
    query_params = dict(request.query_params)

    # Copy headers except Host / Content-Length, override auth headers
    upstream_headers: Dict[str, str] = {}
    for name, value in request.headers.items():
        lname = name.lower()
        if lname in {"host", "content-length"}:
            continue
        upstream_headers[name] = value

    if OPENAI_API_KEY:
        upstream_headers["Authorization"] = f"Bearer {OPENAI_API_KEY}"
    if OPENAI_ORG_ID:
        upstream_headers["OpenAI-Organization"] = OPENAI_ORG_ID

    # Decide how to send the body
    content_type = request.headers.get("content-type", "")
    send_kwargs: Dict[str, Any] = {"headers": upstream_headers, "params": query_params}

    # Read the raw body once (if needed)
    body_bytes: bytes = await request.body()

    # 1) Multipart/form-data (file uploads)
    if content_type.startswith("multipart/form-data"):
        # For tests in this repo we can forward the raw multipart safely.
        # httpx can reuse the same payload via `content=body_bytes`.
        send_kwargs["content"] = body_bytes

    # 2) application/json → use `json=` so forward_spy["json"] sees the dict
    elif "application/json" in content_type.lower():
        try:
            parsed_json = json.loads(body_bytes.decode("utf-8") or "null")
            send_kwargs["json"] = parsed_json
        except Exception:
            # If parsing fails, just send raw content (defensive fallback)
            send_kwargs["content"] = body_bytes

    # 3) Everything else → raw content
    else:
        send_kwargs["content"] = body_bytes

    # Perform the upstream request
    async with httpx.AsyncClient(timeout=float(os.getenv("RELAY_TIMEOUT", "120"))) as client:
        upstream_resp = await client.request(method, target_url, **send_kwargs)

    # Build FastAPI Response
    # Pass through status and headers, but don't forward hop-by-hop ones.
    hop_by_hop = {
        "connection",
        "keep-alive",
        "proxy-authenticate",
        "proxy-authorization",
        "te",
        "trailers",
        "transfer-encoding",
        "upgrade",
    }

    response_headers = {
        k: v for k, v in upstream_resp.headers.items() if k.lower() not in hop_by_hop
    }

    return Response(
        content=upstream_resp.content,
        status_code=upstream_resp.status_code,
        headers=response_headers,
        media_type=upstream_resp.headers.get("content-type"),
    )
