from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, Mapping

import httpx
from fastapi import HTTPException, Request, Response

logger = logging.getLogger("relay")

OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")


def _filter_request_headers(headers: Mapping[str, str]) -> Dict[str, str]:
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
        if kl == "authorization":
            # Always replace with our own Authorization header
            continue
        out[k] = v
    return out


def _filter_response_headers(headers: Mapping[str, str]) -> Dict[str, str]:
    blocked = {
        "connection",
        "keep-alive",
        "proxy-authenticate",
        "proxy-authorization",
        "te",
        "trailers",
        "transfer-encoding",
        "upgrade",
        "content-encoding",  # let ASGI / server handle compression
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
    Generic OpenAI HTTP proxy for /v1/* requests.

    - Copies method, path, query params.
    - Copies headers except hop-by-hop + Authorization.
    - Sends JSON body when Content-Type is application/json, raw bytes otherwise.
    - Injects Authorization: Bearer <OPENAI_API_KEY> if configured.
    - Forces Accept-Encoding=identity so upstream never sends gzipped/brotli data.
    """
    method = upstream_method or request.method
    path = upstream_path or request.url.path

    base = OPENAI_API_BASE.rstrip("/")
    target_url = f"{base}{path}"

    params = dict(request.query_params)

    request_headers = request.headers
    upstream_headers = _filter_request_headers(request_headers)
    if OPENAI_API_KEY:
        upstream_headers["Authorization"] = f"Bearer {OPENAI_API_KEY}"
    upstream_headers["Accept-Encoding"] = "identity"

    raw_body = await request.body()
    json_data: Any | None = None

    content_type = request_headers.get("content-type", "")
    if raw_body and "application/json" in content_type:
        try:
            json_data = json.loads(raw_body.decode("utf-8"))
        except Exception:
            # If JSON parsing fails, fall back to raw bytes
            json_data = None

    request_kwargs: Dict[str, Any] = {}
    if json_data is not None:
        request_kwargs["json"] = json_data
    elif raw_body:
        request_kwargs["content"] = raw_body

    # Longer timeouts for images/videos generation
    if path.startswith("/v1/images") or path.startswith("/v1/videos"):
        timeout = httpx.Timeout(connect=30.0, read=120.0, write=120.0, pool=30.0)
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
