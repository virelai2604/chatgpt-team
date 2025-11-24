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
    # Force plain JSON (no gzip/br) from upstream to avoid decoding issues
    upstream_headers["Accept-Encoding"] = "identity"

    # Body handling
    raw_body = await request.body()
    json_data: Any | None = None

    content_type = request_headers.get("content-type", "")
    if raw_body and "application/json" in content_type:
        try:
            json_data = json.loads(raw_body.decode("utf-8"))
        except Exception:
            json_data = None

    request_kwargs: Dict[str, Any] = {}
    if json_data is not None:
        request_kwargs["json"] = json_data
    elif raw_body:
        request_kwargs["content"] = raw_body

    # Timeout: allow extra time for images/videos
    if path.startswith("/v1/images") or path.startswith("/v1/videos"):
        timeout = httpx.Timeout(
            connect=30.0,
            read=120.0,
            write=120.0,
            pool=30.0,
        )
    else:
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
