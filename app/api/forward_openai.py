"""
forward_openai.py

Shared forwarding logic for all /v1/* routes (models, chat, responses,
files, embeddings, images, videos, etc.).

This keeps behavior aligned with the upstream OpenAI REST API and the
official openai-python SDK, while letting the relay inject its own
authentication and logging.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, Mapping

import httpx
from fastapi import HTTPException, Request, Response

logger = logging.getLogger("relay")

# Base URL for upstream OpenAI API (or compatible endpoint)
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com")

# API key used by the relay when contacting upstream.
# Incoming Authorization header is ignored and replaced.
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")


def _filter_request_headers(headers: Mapping[str, str]) -> Dict[str, str]:
    """
    Remove hop-by-hop or conflicting headers before forwarding to upstream.
    """
    blocked = {
        "host",
        "content-length",
        "connection",
        "keep-alive",
        "proxy-authenticate",
        "proxy-authorization",
        "te",
        "trailers",
        "transfer-encoding",
        "upgrade",
    }

    out: Dict[str, str] = {}
    for k, v in headers.items():
        kl = k.lower()
        if kl in blocked:
            continue
        # We always override Authorization, so we skip any client Authorization.
        if kl == "authorization":
            continue
        out[k] = v
    return out


def _filter_response_headers(headers: Mapping[str, str]) -> Dict[str, str]:
    """
    Filter response headers from upstream before returning to the client.
    """
    blocked = {
        "connection",
        "keep-alive",
        "proxy-authenticate",
        "proxy-authorization",
        "te",
        "trailers",
        "transfer-encoding",
        "upgrade",
        "content-encoding",  # let ASGI/framework handle compression
    }

    out: Dict[str, str] = {}
    for k, v in headers.items():
        if k.lower() in blocked:
            continue
        out[k] = v
    return out


async def forward_openai_request(
    request: Request,
    *,
    upstream_path: str | None = None,
    upstream_method: str | None = None,
) -> Response:
    """
    Generic forwarder for OpenAI-style /v1/* requests.

    Used by all the thin routers (models, files, images, videos, embeddings,
    responses, etc.) so behavior stays aligned with the official REST spec
    and the openai-python client.

    This function:
      - Builds the full upstream URL from OPENAI_API_BASE + request path
      - Copies query params from the incoming request
      - Copies headers (except hop-by-hop) and injects Authorization with
        the relay's OPENAI_API_KEY
      - Forwards JSON body or raw body as appropriate
      - Returns a FastAPI Response with upstream status code, body, and headers
    """
    method = upstream_method or request.method
    path = upstream_path or request.url.path

    # Build upstream URL
    if OPENAI_API_BASE.endswith("/"):
        base = OPENAI_API_BASE[:-1]
    else:
        base = OPENAI_API_BASE
    target_url = f"{base}{path}"

    # Query params passthrough
    params = dict(request.query_params)

    # Headers passthrough + auth override
    request_headers = request.headers
    upstream_headers = _filter_request_headers(request_headers)
    if OPENAI_API_KEY:
        upstream_headers["Authorization"] = f"Bearer {OPENAI_API_KEY}"

    # Body handling
    raw_body = await request.body()
    json_data: Any | None = None

    # Try JSON decode if Content-Type is JSON-like
    content_type = request_headers.get("content-type", "")
    if raw_body and "application/json" in content_type:
        try:
            json_data = json.loads(raw_body.decode("utf-8"))
        except Exception:
            # Malformed JSON; just send raw body through
            json_data = None

    request_kwargs: Dict[str, Any] = {}
    if json_data is not None:
        request_kwargs["json"] = json_data
    elif raw_body:
        # Non-JSON body (e.g. multipart/form-data or binary)
        request_kwargs["content"] = raw_body

    # --- Timeout configuration (THIS IS THE IMPORTANT FIX) ---
    #
    # Images/videos can legitimately take longer than 30 seconds, especially
    # at higher quality/resolution. The previous fixed timeout=30.0 caused
    # httpx.RequestError("Timeout") -> 502 "upstream_connection_error".
    #
    # We now:
    #   - Allow longer read timeouts for /v1/images/* and /v1/videos/*
    #   - Keep a reasonable default timeout for normal calls
    #
    if path.startswith("/v1/images") or path.startswith("/v1/videos"):
        timeout = httpx.Timeout(
            connect=30.0,
            read=120.0,
            write=120.0,
            pool=30.0,
        )
    else:
        # Safe default for chat/responses/etc.
        timeout = httpx.Timeout(30.0)

    logger.info("forward_openai_request.start method=%s path=%s", method, path)

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            upstream_resp = await client.request(
                method=method,
                url=target_url,
                params=params,
                headers=upstream_headers,
                **request_kwargs,
            )
    except httpx.RequestError as exc:
        logger.warning("forward_openai_request.error %s", exc)
        # Normalize any connection/timeout issue as a 502 from the relay.
        raise HTTPException(
            status_code=502,
            detail={
                "error": {
                    "message": "Error contacting upstream OpenAI API",
                    "type": "upstream_connection_error",
                }
            },
        ) from exc

    logger.info(
        "forward_openai_request.done method=%s path=%s status=%s",
        method,
        path,
        upstream_resp.status_code,
    )

    response_headers = _filter_response_headers(upstream_resp.headers)

    return Response(
        content=upstream_resp.content,
        status_code=upstream_resp.status_code,
        headers=response_headers,
    )
