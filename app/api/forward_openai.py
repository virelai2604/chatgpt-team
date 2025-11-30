# app/api/forward_openai.py

from __future__ import annotations

import json
import logging
from typing import Any, Dict, Mapping, Optional

import httpx
from fastapi import HTTPException, Request, Response

from app.core.config import settings

logger = logging.getLogger("relay")

# Single source of truth – use Pydantic settings (P4 core plan)
OPENAI_API_BASE: str = str(settings.OPENAI_API_BASE).rstrip("/")
OPENAI_API_KEY: str = settings.OPENAI_API_KEY


def _filter_request_headers(headers: Mapping[str, str]) -> Dict[str, str]:
    """
    Drop hop-by-hop headers and downstream Authorization before forwarding.

    We will always inject our own Authorization header, derived from
    OPENAI_API_KEY, so the relay never forwards arbitrary client secrets
    upstream.
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
        if kl == "authorization":
            # Always replace with our own Authorization header
            continue
        out[k] = v
    return out


def _filter_response_headers(headers: Mapping[str, str]) -> Dict[str, str]:
    """
    Drop hop-by-hop headers and content-encoding from the upstream response.

    We let the ASGI server handle compression; we want to avoid re-exposing
    gzip/brotli directly and keep the downstream JSON/text simple.
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
        "content-encoding",  # let ASGI / server handle compression
    }

    out: Dict[str, str] = {}
    for k, v in headers.items():
        if k.lower() in blocked:
            continue
        out[k] = v
    return out


async def _do_forward(
    *,
    method: str,
    path: str,
    query_params: Optional[Dict[str, Any]],
    incoming_headers: Mapping[str, str],
    raw_body: Optional[bytes],
    json_body: Any,
) -> Response:
    """
    Core HTTP proxy implementation used by both:

      - forward_openai_request (Request → upstream)
      - forward_openai_from_parts (payload → upstream)
    """
    if not path.startswith("/"):
        path = "/" + path

    target_url = f"{OPENAI_API_BASE}{path}"

    if not OPENAI_API_KEY:
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "message": "OPENAI_API_KEY is not configured",
                    "type": "config_error",
                    "code": "no_api_key",
                }
            },
        )

    params = query_params or {}

    upstream_headers = _filter_request_headers(incoming_headers)

    upstream_headers["Authorization"] = f"Bearer {OPENAI_API_KEY}"
    upstream_headers["Accept-Encoding"] = "identity"

    request_kwargs: Dict[str, Any] = {}
    if json_body is not None:
        request_kwargs["json"] = json_body
    elif raw_body:
        request_kwargs["content"] = raw_body

    # Longer timeouts for images/videos generation
    # Use settings.PROXY_TIMEOUT as baseline
    if path.startswith("/v1/images") or path.startswith("/v1/videos"):
        timeout = httpx.Timeout(
            connect=30.0,
            read=float(settings.PROXY_TIMEOUT),
            write=float(settings.PROXY_TIMEOUT),
            pool=30.0,
        )
    else:
        timeout = httpx.Timeout(float(settings.PROXY_TIMEOUT))

    logger.info(
        "forward_openai_core.start method=%s path=%s params=%s",
        method,
        path,
        params,
    )

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
        logger.warning("forward_openai_core.error %s", exc)
        # Map connection errors to a clear OpenAI-style error envelope
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
        "forward_openai_core.done method=%s path=%s status=%s",
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
    - Injects Authorization: Bearer <OPENAI_API_KEY>.
    - Forces Accept-Encoding=identity so upstream never sends gzipped/brotli data.
    """
    method = (upstream_method or request.method).upper()
    path = upstream_path or request.url.path

    query_params = dict(request.query_params)
    incoming_headers = request.headers

    raw_body = await request.body()
    json_body: Any = None

    content_type = incoming_headers.get("content-type", "")
    if raw_body and "application/json" in content_type:
        try:
            json_body = json.loads(raw_body.decode("utf-8"))
            raw_body = None
        except Exception:
            # Fallback to sending raw bytes if JSON parsing fails
            json_body = None

    return await _do_forward(
        method=method,
        path=path,
        query_params=query_params,
        incoming_headers=incoming_headers,
        raw_body=raw_body,
        json_body=json_body,
    )


async def forward_openai_from_parts(
    *,
    method: str,
    path: str,
    query: Optional[Dict[str, Any]] = None,
    body: Any | None = None,
    headers: Optional[Mapping[str, str]] = None,
) -> Response:
    """
    Forwarder for ChatGPT Actions / agent tools that send:

      {
        "method": "GET" | "POST" | ...,
        "path": "/v1/models",
        "query": {...},
        "body": {...}
      }

    This does NOT trust arbitrary Authorization headers; any provided
    headers are filtered through the same rules as forward_openai_request.
    """
    method = method.upper()
    incoming_headers: Mapping[str, str] = headers or {}

    return await _do_forward(
        method=method,
        path=path,
        query_params=query or {},
        incoming_headers=incoming_headers,
        raw_body=None,
        json_body=body,
    )
