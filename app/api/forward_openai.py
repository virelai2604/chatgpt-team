from typing import Any, Dict, Optional

import os

import httpx
from fastapi import Request
from fastapi.responses import Response

# Base configuration – these map to your environment variables
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
PROXY_TIMEOUT = float(os.getenv("PROXY_TIMEOUT", "120"))


# Hop-by-hop headers that must not be forwarded to the client
HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
}


async def forward_openai_request(
    request: Request,
    path: Optional[str] = None,
    method: Optional[str] = None,
    raw_body: Optional[bytes] = None,
    json_body: Optional[Any] = None,
    content_type: Optional[str] = None,
) -> Response:
    """
    Generic forwarder for OpenAI API.

    - For JSON requests: pass json_body (or pull from request).
    - For multipart/file uploads: pass raw_body (raw bytes) and content_type.
    - For anything else: forward raw body as-is.

    This function:
    - Builds the upstream URL from OPENAI_API_BASE + /v1 + path.
    - Copies request headers but removes host/content-length/transfer-encoding.
    - Forces Authorization from OPENAI_API_KEY if present.
    - Returns a FastAPI Response mirroring upstream status/body/content-type.
    """

    # 1) Determine path and method from request if not explicitly provided
    upstream_path = path or request.url.path
    upstream_method = (method or request.method).upper()

    # Normalize path: ensure we call OPENAI_API_BASE + /v1/...
    base = OPENAI_API_BASE.rstrip("/")
    if upstream_path.startswith("/v1/"):
        upstream_url = f"{base}{upstream_path}"
    elif upstream_path.startswith("/"):
        upstream_url = f"{base}/v1{upstream_path}"
    else:
        upstream_url = f"{base}/v1/{upstream_path}"

    # 2) Build headers – copy from incoming, strip hop-by-hop and length headers
    headers: Dict[str, str] = {}
    for k, v in request.headers.items():
        kl = k.lower()
        if kl in HOP_BY_HOP_HEADERS or kl in {"host", "content-length"}:
            continue
        headers[k] = v

    # Force Authorization from env if provided
    if OPENAI_API_KEY:
        headers["Authorization"] = f"Bearer {OPENAI_API_KEY}"

    # Override content-type if caller specified it
    if content_type:
        headers["Content-Type"] = content_type

    # 3) Prepare query params
    params = dict(request.query_params)

    # 4) Perform upstream request using httpx
    async with httpx.AsyncClient(timeout=PROXY_TIMEOUT) as client:
        if raw_body is not None:
            # Multipart or opaque body: send raw bytes.
            upstream_response = await client.request(
                upstream_method,
                upstream_url,
                headers=headers,
                params=params,
                content=raw_body,
            )
        elif json_body is not None:
            upstream_response = await client.request(
                upstream_method,
                upstream_url,
                headers=headers,
                params=params,
                json=json_body,
            )
        else:
            # Fallback: forward raw body exactly once
            body_bytes = await request.body()
            upstream_response = await client.request(
                upstream_method,
                upstream_url,
                headers=headers,
                params=params,
                content=body_bytes,
            )

    # 5) Build response to client – mirror status code and content-type
    upstream_content_type = upstream_response.headers.get("content-type")
    response_headers: Dict[str, str] = {}

    # Copy relevant headers, excluding hop-by-hop and content-length
    for k, v in upstream_response.headers.items():
        kl = k.lower()
        if kl in HOP_BY_HOP_HEADERS or kl == "content-length":
            continue
        # Let FastAPI handle content-type, we set it via media_type below
        if kl == "content-type":
            continue
        response_headers[k] = v

    return Response(
        content=upstream_response.content,
        status_code=upstream_response.status_code,
        media_type=upstream_content_type,
        headers=response_headers,
    )
