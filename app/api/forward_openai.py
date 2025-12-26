from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, Iterable, Mapping, Optional

import httpx
from fastapi import HTTPException, Request, Response
from starlette.responses import StreamingResponse

from app.core.config import get_settings
from app.core.http_client import get_async_httpx_client

logger = logging.getLogger(__name__)


def _get_setting(name: str, default: Optional[str] = None) -> Optional[str]:
    settings = get_settings()
    val = getattr(settings, name, None)
    if val is None:
        return default
    return val


def _openai_base_url() -> str:
    # Prefer explicit OPENAI_API_BASE (often ends with /v1)
    base = _get_setting("OPENAI_API_BASE", None) or "https://api.openai.com/v1"
    return base.rstrip("/")


def _join_url(base: str, path: str, query: str = "") -> str:
    """
    Join base + path safely.

    Handles:
      - base ending with /v1 while path starts with /v1/ (avoid /v1/v1)
      - duplicate slashes
      - optional query string
    """
    base = base.rstrip("/")
    if not path.startswith("/"):
        path = "/" + path

    # Avoid /v1/v1/... when base already contains /v1 and path includes /v1
    if base.endswith("/v1") and path.startswith("/v1/"):
        path = path[len("/v1") :]

    url = f"{base}{path}"
    if query:
        if query.startswith("?"):
            url += query
        else:
            url += "?" + query
    return url


def build_upstream_url(upstream_path: str, request: Optional[Request] = None) -> str:
    base = _openai_base_url()
    query = ""
    if request is not None:
        query = request.url.query or ""
    return _join_url(base, upstream_path, query=query)


HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
}


def _filter_response_headers(headers: Mapping[str, str]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for k, v in headers.items():
        lk = k.lower()
        if lk in HOP_BY_HOP_HEADERS:
            continue
        # Some servers send multiple set-cookie headers; httpx collapses.
        # For our tests, this is acceptable.
        out[k] = v
    return out


def _build_outbound_headers(
    inbound_headers: Mapping[str, str],
    *,
    content_type: Optional[str] = None,
    forward_accept: bool = True,
) -> Dict[str, str]:
    """
    Build headers for upstream OpenAI call.

    We do NOT forward the inbound Authorization because inbound auth is for the relay.
    Upstream Authorization uses OPENAI_API_KEY from settings.
    """
    settings = get_settings()
    out: Dict[str, str] = {}

    # Preserve a few safe headers
    for k, v in inbound_headers.items():
        lk = k.lower()
        if lk in HOP_BY_HOP_HEADERS:
            continue
        if lk in ("authorization", "host", "content-length"):
            continue
        if lk == "accept" and not forward_accept:
            continue
        out[k] = v

    # Force upstream auth
    out["Authorization"] = f"Bearer {settings.OPENAI_API_KEY}"

    # Optional org/project headers
    if getattr(settings, "OPENAI_ORG_ID", None):
        out["OpenAI-Organization"] = settings.OPENAI_ORG_ID
    if getattr(settings, "OPENAI_PROJECT_ID", None):
        out["OpenAI-Project"] = settings.OPENAI_PROJECT_ID

    # Avoid gzip issues when streaming; identity keeps it simple
    out["Accept-Encoding"] = "identity"

    if content_type:
        out["Content-Type"] = content_type

    return out


async def forward_openai_method_path(
    method: str,
    upstream_path: str,
    *,
    request: Optional[Request] = None,
    json_body: Any = None,
    data: Any = None,
    files: Any = None,
    content_type: Optional[str] = None,
    inbound_headers: Optional[Mapping[str, str]] = None,
) -> Response:
    """
    Forward a request to upstream OpenAI for a known method+path.

    Supports:
      - JSON bodies
      - raw bytes body (via data)
      - multipart (via files)
    """
    url = build_upstream_url(upstream_path, request=request)

    hdrs = inbound_headers or (request.headers if request is not None else {})
    headers = _build_outbound_headers(hdrs, content_type=content_type)

    client = get_async_httpx_client()

    try:
        resp = await client.request(
            method.upper(),
            url,
            headers=headers,
            json=json_body,
            content=data,
            files=files,
            timeout=None,
        )
    except httpx.HTTPError as e:
        logger.exception("Upstream HTTP error: %s", e)
        raise HTTPException(status_code=502, detail=f"Upstream OpenAI error: {e!s}")

    filtered = _filter_response_headers(resp.headers)
    return Response(content=resp.content, status_code=resp.status_code, headers=filtered)


async def forward_openai_request(request: Request) -> Response:
    """
    Generic pass-through handler: forwards the incoming Starlette request to upstream OpenAI.

    Used by many routes that simply mirror OpenAI paths.
    """
    upstream_path = request.url.path  # includes /v1/...
    url = build_upstream_url(upstream_path, request=request)

    body = await request.body()

    headers = _build_outbound_headers(request.headers)

    client = get_async_httpx_client()

    # If client asked for streaming and upstream responds with SSE, stream it.
    accept = request.headers.get("accept", "")
    wants_stream = "text/event-stream" in accept.lower() or request.url.path.endswith(":stream")

    try:
        if wants_stream:
            upstream = client.stream(
                request.method.upper(),
                url,
                headers=headers,
                content=body,
                timeout=None,
            )

            async def _iter_bytes() -> Iterable[bytes]:
                async with upstream as r:
                    r.raise_for_status()
                    async for chunk in r.aiter_bytes():
                        yield chunk

            async with upstream as r:
                filtered = _filter_response_headers(r.headers)
                media_type = r.headers.get("content-type", "text/event-stream")
                return StreamingResponse(_iter_bytes(), status_code=r.status_code, headers=filtered, media_type=media_type)

        resp = await client.request(
            request.method.upper(),
            url,
            headers=headers,
            content=body,
            timeout=None,
        )
    except httpx.HTTPStatusError as e:
        # Preserve upstream status
        logger.warning("Upstream status error: %s", e)
        status = e.response.status_code if e.response is not None else 502
        detail = e.response.text if e.response is not None else str(e)
        raise HTTPException(status_code=status, detail=detail)
    except httpx.HTTPError as e:
        logger.exception("Upstream HTTP error: %s", e)
        raise HTTPException(status_code=502, detail=f"Upstream OpenAI error: {e!s}")

    filtered = _filter_response_headers(resp.headers)
    return Response(content=resp.content, status_code=resp.status_code, headers=filtered)


# Backwards-compat aliases for modules that import these symbols directly
build_outbound_headers = _build_outbound_headers
filter_upstream_headers = _filter_response_headers
