# app/api/forward_openai.py

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, Mapping, Optional, Union

import httpx
from fastapi import HTTPException, Request, Response
from fastapi.responses import StreamingResponse

from app.core.config import settings

logger = logging.getLogger("relay")

# ---------------------------------------------------------------------------
# Upstream configuration
# ---------------------------------------------------------------------------

# Base URL for OpenAI (no /v1 suffix – paths below always start with /v1)
OPENAI_API_BASE: str = str(settings.OPENAI_API_BASE).rstrip("/")

# API key used by the relay when forwarding to OpenAI
OPENAI_API_KEY: str = settings.OPENAI_API_KEY

# Timeout (seconds) for upstream OpenAI calls
DEFAULT_PROXY_TIMEOUT = float(os.getenv("PROXY_TIMEOUT", os.getenv("RELAY_TIMEOUT", "120")))
PROXY_TIMEOUT: float = float(getattr(settings, "PROXY_TIMEOUT", DEFAULT_PROXY_TIMEOUT))


# ---------------------------------------------------------------------------
# Header helpers
# ---------------------------------------------------------------------------


def _filter_request_headers(headers: Mapping[str, str]) -> Dict[str, str]:
    """
    Prepare headers for forwarding to OpenAI.

    - Drop hop-by-hop headers that should not cross proxies.
    - Drop downstream Authorization and X-Relay-Key; the relay injects its own.
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
        "x-relay-key",
    }

    out: Dict[str, str] = {}
    for name, value in headers.items():
        lname = name.lower()
        if lname in blocked:
            continue
        if lname == "authorization":
            # Always replace with relay's Authorization header
            continue
        out[name] = value
    return out


def _filter_response_headers(headers: Mapping[str, str]) -> Dict[str, str]:
    """
    Prepare headers coming back from OpenAI before returning to the client.

    We drop hop-by-hop and transport headers; Uvicorn/ASGI will manage
    Content-Length, Transfer-Encoding, and connection reuse.
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
        "content-encoding",
        "content-length",
    }

    out: Dict[str, str] = {}
    for name, value in headers.items():
        if name.lower() in blocked:
            continue
        out[name] = value
    return out


def _ensure_api_key() -> None:
    """
    Ensure the relay has an OpenAI API key configured.
    """
    if not OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY is not configured on the relay")
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "message": "OPENAI_API_KEY is not configured on the relay",
                    "type": "server_error",
                    "code": "no_api_key",
                }
            },
        )


def _is_sse_request(request: Request) -> bool:
    """
    Detect Server-Sent Events (SSE) requests by Accept header.

    SSE is used by the Responses API when `stream=true` and the client
    requests `Accept: text/event-stream`.
    """
    accept = request.headers.get("accept", "")
    return "text/event-stream" in accept.lower()


def _extract_output_text_from_response_json(data: Dict[str, Any]) -> str:
    """
    Extract plain text from a Responses JSON payload.

    See the Responses output structure:
    - top-level "output" array with items containing "content" parts
      of type "output_text" that hold the text. 
    """
    output = data.get("output")
    if isinstance(output, list):
        texts: list[str] = []
        for item in output:
            if not isinstance(item, dict):
                continue
            for part in item.get("content") or []:
                if not isinstance(part, dict):
                    continue
                if part.get("type") == "output_text":
                    txt = part.get("text") or ""
                    if isinstance(txt, str):
                        texts.append(txt)
        if texts:
            return "".join(texts)

    # Fallbacks if future API adds convenience fields
    text = data.get("output_text") or data.get("text")
    if isinstance(text, str):
        return text

    return ""


# ---------------------------------------------------------------------------
# Core /v1 proxy
# ---------------------------------------------------------------------------


async def forward_openai_request(
    request: Request,
    *,
    method: Optional[str] = None,
    path_override: Optional[str] = None,
) -> Response:
    """
    Generic forwarder used by all /v1/* routers.

    - Respects the incoming HTTP method (unless overridden).
    - Forwards to OPENAI_API_BASE + path.
    - For SSE (Accept: text/event-stream), streams upstream bytes via
      StreamingResponse. If upstream SSE fails before any data arrives,
      falls back to a non-streaming call and synthesizes SSE events.
    """
    _ensure_api_key()

    method = (method or request.method).upper()
    path = path_override or request.url.path

    if not path.startswith("/v1"):
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "message": "Only /v1 paths are proxied",
                    "type": "invalid_request_error",
                    "param": None,
                    "code": None,
                }
            },
        )

    headers = _filter_request_headers(request.headers)
    headers["Authorization"] = f"Bearer {OPENAI_API_KEY}"

    params = dict(request.query_params)
    body = await request.body()

    timeout = httpx.Timeout(PROXY_TIMEOUT)
    is_sse = _is_sse_request(request)

    async with httpx.AsyncClient(base_url=OPENAI_API_BASE, timeout=timeout) as client:
        if is_sse:
            # Try true upstream SSE first
            upstream_ctx = client.stream(
                method,
                path,
                params=params,
                headers=headers,
                content=body if body else None,
            )
            upstream = await upstream_ctx.__aenter__()

            resp_headers = _filter_response_headers(upstream.headers)
            media_type = upstream.headers.get("content-type", "text/event-stream")

            async def _aiter():
                got_any = False
                closed = False

                try:
                    # Primary path: proxy SSE bytes from upstream
                    async for chunk in upstream.aiter_bytes():
                        if chunk:
                            got_any = True
                            yield chunk
                except (httpx.ReadError, httpx.HTTPError) as exc:
                    logger.warning(
                        "Upstream SSE error (%s %s): %r", method, path, exc
                    )

                    # Ensure upstream stream is closed before fallback
                    try:
                        await upstream_ctx.__aexit__(None, None, None)
                        closed = True
                    except Exception:
                        pass

                    # If we already forwarded some bytes, just end the stream.
                    if got_any:
                        return

                    # Fallback: call /v1/responses without stream and synthesize SSE.
                    fb_headers = {k: v for k, v in headers.items() if k.lower() != "accept"}
                    fb_body_bytes: Optional[bytes] = body

                    if body:
                        try:
                            obj = json.loads(body.decode("utf-8"))
                            if isinstance(obj, dict):
                                # Avoid triggering upstream SSE again
                                obj.pop("stream", None)
                            fb_body_bytes = json.dumps(obj).encode("utf-8")
                        except Exception:
                            fb_body_bytes = body

                    try:
                        resp_fb = await client.request(
                            method,
                            path,
                            params=params,
                            headers=fb_headers,
                            content=fb_body_bytes if fb_body_bytes else None,
                        )
                    except httpx.RequestError as exc2:
                        logger.error(
                            "Fallback non-stream /responses failed: %r", exc2
                        )
                        return

                    if resp_fb.status_code != 200:
                        logger.warning(
                            "Fallback non-stream /responses returned %s %s",
                            resp_fb.status_code,
                            resp_fb.text,
                        )
                        return

                    try:
                        data = resp_fb.json()
                    except Exception as exc3:
                        logger.warning("Fallback JSON decode error: %r", exc3)
                        return

                    text_out = _extract_output_text_from_response_json(data)
                    if not text_out:
                        logger.warning(
                            "Fallback non-stream /responses returned empty text"
                        )
                        return

                    # Synthesize Responses SSE events matching the docs
                    # and the relay_e2e_raw expectations. :contentReference[oaicite:5]{index=5}
                    ev_delta = json.dumps(
                        {
                            "type": "response.output_text.delta",
                            "delta": text_out,
                        }
                    )
                    yield f"data: {ev_delta}\n\n".encode("utf-8")

                    ev_done = json.dumps(
                        {
                            "type": "response.output_text.done",
                            "text": text_out,
                        }
                    )
                    yield f"data: {ev_done}\n\n".encode("utf-8")

                    # Standard SSE sentinel for end-of-stream
                    yield b"data: [DONE]\n\n"

                finally:
                    if not closed:
                        try:
                            await upstream_ctx.__aexit__(None, None, None)
                        except Exception:
                            pass

            return StreamingResponse(
                _aiter(),
                status_code=upstream.status_code,
                headers=resp_headers,
                media_type=media_type,
            )

        # Non-streaming path: single request/response
        try:
            upstream_response = await client.request(
                method,
                path,
                params=params,
                headers=headers,
                content=body if body else None,
            )
        except httpx.RequestError as exc:
            logger.error("Error forwarding request to OpenAI: %r", exc)
            raise HTTPException(
                status_code=502,
                detail={
                    "error": {
                        "message": "Error forwarding request to OpenAI",
                        "type": "server_error",
                        "code": "upstream_request_error",
                        "extra": {"exception": str(exc)},
                    }
                },
            ) from exc

    resp_headers = _filter_response_headers(upstream_response.headers)

    return Response(
        content=upstream_response.content,
        status_code=upstream_response.status_code,
        headers=resp_headers,
        media_type=upstream_response.headers.get("content-type"),
    )


# ---------------------------------------------------------------------------
# Programmatic forwarding for /v1/actions/openai/forward
# ---------------------------------------------------------------------------


async def forward_openai_from_parts(
    method: str,
    path: str,
    *,
    query: Optional[Mapping[str, Any]] = None,
    headers: Optional[Mapping[str, str]] = None,
    body: Optional[Union[str, bytes, Mapping[str, Any], Any]] = None,
    stream: bool = False,
) -> Response:
    """
    Programmatic forwarding used by the Actions router.

    Parameters
    ----------
    method:
        HTTP method, e.g. "GET", "POST".
    path:
        OpenAI-compatible path. Must start with "/v1".
    query:
        Optional query parameters.
    headers:
        Optional additional headers from the caller. Authorization / X-Relay-Key
        are stripped and replaced with relay's credentials.
    body:
        Request body; may be raw bytes/str or JSON-serializable.
    stream:
        If True, create an SSE stream to OpenAI and proxy it to the caller.
    """
    _ensure_api_key()

    if not path.startswith("/v1"):
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "message": "path must start with /v1",
                    "type": "invalid_request_error",
                    "param": None,
                    "code": None,
                }
            },
        )

    method = method.upper()

    base_headers = _filter_request_headers(headers or {})
    base_headers["Authorization"] = f"Bearer {OPENAI_API_KEY}"

    timeout = httpx.Timeout(PROXY_TIMEOUT)
    params = dict(query or {})

    # Normalize body into either JSON or raw content
    json_body: Any = None
    content_body: Optional[Union[str, bytes]] = None

    if isinstance(body, (bytes, str)) or body is None:
        content_body = body
    else:
        json_body = body

    async with httpx.AsyncClient(base_url=OPENAI_API_BASE, timeout=timeout) as client:
        if stream:
            upstream_ctx = client.stream(
                method,
                path,
                params=params,
                headers=base_headers,
                json=json_body,
                content=content_body,
            )
            upstream = await upstream_ctx.__aenter__()

            resp_headers = _filter_response_headers(upstream.headers)
            media_type = upstream.headers.get("content-type", "text/event-stream")

            async def _aiter():
                closed = False
                try:
                    async for chunk in upstream.aiter_bytes():
                        if chunk:
                            yield chunk
                except (httpx.ReadError, httpx.HTTPError) as exc:
                    logger.warning(
                        "Upstream SSE error (from_parts %s %s): %r", method, path, exc
                    )
                finally:
                    if not closed:
                        try:
                            await upstream_ctx.__aexit__(None, None, None)
                        except Exception:
                            pass

            return StreamingResponse(
                _aiter(),
                status_code=upstream.status_code,
                headers=resp_headers,
                media_type=media_type,
            )

        # Non-streaming call
        try:
            upstream_response = await client.request(
                method,
                path,
                params=params,
                headers=base_headers,
                json=json_body,
                content=content_body,
            )
        except httpx.RequestError as exc:
            logger.error("Error forwarding request (from_parts) to OpenAI: %r", exc)
            raise HTTPException(
                status_code=502,
                detail={
                    "error": {
                        "message": "Error forwarding request to OpenAI",
                        "type": "server_error",
                        "code": "upstream_request_error",
                        "extra": {"exception": str(exc)},
                    }
                },
            ) from exc

    resp_headers = _filter_response_headers(upstream_response.headers)

    return Response(
        content=upstream_response.content,
        status_code=upstream_response.status_code,
        headers=resp_headers,
        media_type=upstream_response.headers.get("content-type"),
    )
