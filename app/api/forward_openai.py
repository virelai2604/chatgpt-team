# app/api/forward_openai.py

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Dict, Mapping, Optional

import httpx
from fastapi import HTTPException, Request, Response
from fastapi.responses import StreamingResponse

from app.core.config import settings

logger = logging.getLogger("relay")

# Single source of truth – use Pydantic settings
OPENAI_API_BASE: str = str(settings.OPENAI_API_BASE).rstrip("/")
OPENAI_API_KEY: str = settings.OPENAI_API_KEY

# Base timeout in seconds; you can tune in app/core/config.py
PROXY_TIMEOUT: float = float(getattr(settings, "PROXY_TIMEOUT", 120))


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


def _choose_timeout(path: str) -> float:
    """
    Simple heuristic: allow more time for long-running endpoints.
    Tune as needed.
    """
    base = PROXY_TIMEOUT
    if path.startswith("/v1/videos"):
        return max(base, 600.0)
    if path.startswith("/v1/images"):
        return max(base, 300.0)
    if path.startswith("/v1/realtime"):
        return max(base, 300.0)
    return base


def _is_sse_request(
    path: str,
    incoming_headers: Mapping[str, str],
    json_body: Any,
) -> bool:
    """
    Decide whether this should be treated as an SSE stream.

    Rules:
    - Accept: text/event-stream  ⇒ always treat as SSE
    - path startswith /v1/responses AND body.stream == true ⇒ treat as SSE
    """
    accept = (incoming_headers.get("accept") or "").lower()
    if "text/event-stream" in accept:
        return True

    if (
        path.startswith("/v1/responses")
        and isinstance(json_body, dict)
        and json_body.get("stream") is True
    ):
        return True

    return False


async def _do_forward(
    *,
    method: str,
    path: str,
    query_params: Optional[Dict[str, Any]],
    incoming_headers: Mapping[str, str],
    raw_body: Optional[bytes],
    json_body: Any,
    request: Optional[Request] = None,
) -> Response:
    """
    Core HTTP proxy implementation used by both:

      - forward_openai_request (Request → upstream)
      - forward_openai_from_parts (payload → upstream)
    """
    if not path:
        path = "/"
    if not path.startswith("/"):
        path = "/" + path.lstrip("/")

    if not OPENAI_API_KEY:
        # OpenAI-style error envelope for missing API key
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "message": "OpenAI API key not configured on relay.",
                    "type": "server_error",
                    "param": None,
                    "code": "missing_api_key",
                }
            },
        )

    target_url = f"{OPENAI_API_BASE}{path}"
    timeout = _choose_timeout(path)

    # Prepare headers
    upstream_headers = _filter_request_headers(incoming_headers)
    upstream_headers["Authorization"] = f"Bearer {OPENAI_API_KEY}"
    # Ensure we don't get gzipped/brotli data; keep things simple
    upstream_headers.setdefault("Accept-Encoding", "identity")

    # Prepare request kwargs
    request_kwargs: Dict[str, Any] = {
        "params": query_params or {},
        "headers": upstream_headers,
        "timeout": timeout,
    }
    if json_body is not None:
        request_kwargs["json"] = json_body
    elif raw_body is not None:
        request_kwargs["content"] = raw_body

    # Decide if this is an SSE stream (responses streaming)
    wants_sse = _is_sse_request(path, incoming_headers, json_body)

    logger.info(
        "forward_openai_core.start method=%s path=%s params=%s sse=%s",
        method,
        path,
        request_kwargs["params"],
        wants_sse,
    )

    if wants_sse:
        # SSE streaming path using StreamingResponse + httpx.stream
        async def event_generator() -> Any:
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    async with client.stream(
                        method,
                        target_url,
                        **request_kwargs,
                    ) as upstream_resp:
                        # We intentionally do not try to re-map non-200 status codes
                        # for SSE – if upstream fails, the stream simply ends or
                        # the client sees an error on connect.
                        async for line in upstream_resp.aiter_lines():
                            if request is not None:
                                # Stop if downstream client disconnects
                                try:
                                    if await request.is_disconnected():
                                        logger.info(
                                            "forward_openai_core.sse_client_disconnected "
                                            "path=%s",
                                            path,
                                        )
                                        break
                                except RuntimeError:
                                    # is_disconnected can raise if called outside request
                                    pass

                            if not line:
                                # Preserve SSE framing blank lines
                                yield "\n"
                                continue

                            # OpenAI already sends proper "data: ..." lines.
                            # We just forward them with a newline.
                            yield f"{line}\n"

                            # Yield control to event loop
                            await asyncio.sleep(0)
            except Exception as exc:
                logger.warning("forward_openai_core.sse_error %s", exc)

        # Always return 200 for SSE streams; upstream errors will surface
        # as connection failures or stream termination.
        return StreamingResponse(
            event_generator(),
            status_code=200,
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            },
        )

    # Normal (non-SSE) path
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            upstream_resp = await client.request(
                method,
                target_url,
                **request_kwargs,
            )
    except httpx.RequestError as exc:
        logger.warning("forward_openai_core.error %s", exc)
        raise HTTPException(
            status_code=502,
            detail={
                "error": {
                    "message": "Error forwarding request to OpenAI.",
                    "type": "bad_gateway",
                    "param": None,
                    "code": "upstream_connection_error",
                }
            },
        ) from exc

    response_headers = _filter_response_headers(upstream_resp.headers)
    logger.info(
        "forward_openai_core.done method=%s path=%s status=%s",
        method,
        path,
        upstream_resp.status_code,
    )

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
    - If Accept: text/event-stream or body.stream==true on /v1/responses, uses SSE.
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
        request=request,
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
        request=None,
    )
