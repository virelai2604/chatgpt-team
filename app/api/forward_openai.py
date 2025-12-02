# app/api/forward_openai.py
from __future__ import annotations

import json
import logging
from typing import Any, Dict, Mapping, Optional

import httpx
from fastapi import HTTPException, Request, Response

from app.core.config import settings

logger = logging.getLogger("relay")

# Single source of truth – use Pydantic settings
OPENAI_API_BASE: str = str(settings.OPENAI_API_BASE).rstrip("/")
OPENAI_API_KEY: str = settings.OPENAI_API_KEY


def _filter_request_headers(headers: Mapping[str, str]) -> Dict[str, str]:
    """
    Drop hop-by-hop headers and downstream Authorization before forwarding.

    The relay always injects its own Authorization header, derived from
    OPENAI_API_KEY, so arbitrary client secrets are never forwarded upstream.
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

    We let the ASGI server handle compression; we avoid re-exposing gzip/brotli
    directly and keep the downstream JSON/text simple.
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
    upstream_headers.setdefault("Accept", "application/json")
    upstream_headers["Authorization"] = f"Bearer {OPENAI_API_KEY}"
    upstream_headers["Accept-Encoding"] = "identity"

    request_kwargs: Dict[str, Any] = {}
    if json_body is not None:
        request_kwargs["json"] = json_body
    elif raw_body:
        request_kwargs["content"] = raw_body

    # Longer timeouts for images/videos generation
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
        logger.exception("Error proxying request to OpenAI: %s", exc)
        raise HTTPException(
            status_code=502,
            detail={
                "error": {
                    "message": "Failed to reach OpenAI API",
                    "type": "upstream_error",
                    "code": "openai_upstream_unreachable",
                }
            },
        ) from exc

    logger.info(
        "forward_openai_core.done method=%s path=%s status=%s",
        method,
        path,
        upstream_resp.status_code,
    )

    filtered_headers = _filter_response_headers(upstream_resp.headers)
    return Response(
        content=upstream_resp.content,
        status_code=upstream_resp.status_code,
        headers=filtered_headers,
        media_type=upstream_resp.headers.get("content-type"),
    )


async def forward_openai_request(request: Request) -> Response:
    """
    Public entrypoint for normal FastAPI routes.

    Forwards the incoming Request to the upstream OpenAI API, preserving:
      - HTTP method
      - path
      - query parameters
      - headers (after filtering)
      - JSON/body
    """
    method = request.method
    path = request.url.path
    query_params = dict(request.query_params)

    # Try to parse JSON; fall back to raw bytes
    raw_body = await request.body()
    json_body: Any = None
    content_type = request.headers.get("content-type", "")
    if raw_body and "application/json" in content_type.lower():
        try:
            json_body = json.loads(raw_body.decode("utf-8"))
            raw_body = None
        except Exception:
            # Leave as raw bytes if JSON parse fails
            json_body = None

    return await _do_forward(
        method=method,
        path=path,
        query_params=query_params,
        incoming_headers=request.headers,
        raw_body=raw_body or None,
        json_body=json_body,
    )


async def forward_openai_from_parts(
    method: str,
    path: str,
    query: Optional[Dict[str, Any]] = None,
    body: Any = None,
    headers: Optional[Dict[str, str]] = None,
) -> Response:
    """
    Public entrypoint for the generic Forward API:

      /v1/actions/openai/forward

    This is primarily used by ChatGPT Actions / custom agents so that a single
    tool can reach any OpenAI endpoint through this relay.
    """
    incoming_headers: Dict[str, str] = dict(headers or {})
    # Ensure we at least send a content-type when JSON is present
    if body is not None and "content-type" not in {
        k.lower() for k in incoming_headers.keys()
    }:
        incoming_headers["Content-Type"] = "application/json"

    return await _do_forward(
        method=method.upper(),
        path=path,
        query_params=query,
        incoming_headers=incoming_headers,
        raw_body=None,
        json_body=body,
    )
