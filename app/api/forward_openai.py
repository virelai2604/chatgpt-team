from __future__ import annotations

from typing import Any, Dict, Optional
import json
import logging
import os

import httpx
from fastapi import Request
from fastapi.responses import Response

# ---------------------------------------------------------------------------
# Base configuration – these map to your environment variables
# ---------------------------------------------------------------------------

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

logger = logging.getLogger("relay.forward_openai")


async def forward_openai_request(
    request: Request,
    path: Optional[str] = None,
    method: Optional[str] = None,
    raw_body: Optional[bytes] = None,
    json_body: Optional[Any] = None,
    content_type: Optional[str] = None,
) -> Response:
    """
    Generic forwarder for the OpenAI API, used by all relay endpoints.

    Behavior
    --------
    - Builds an upstream URL from OPENAI_API_BASE and the incoming path.
      * If the path starts with `/v1/`, it is appended directly.
      * Otherwise, `/v1` is prefixed to match the official REST surface.

    - Copies inbound headers while stripping hop-by-hop headers, Host, and
      Content-Length. Authorization is always re-derived from OPENAI_API_KEY.

    - For the request body:
      * If `raw_body` is provided, it is forwarded as opaque bytes via
        `content=raw_body`. This is used for multipart/form-data (files) and
        other non-JSON payloads.
      * Else if `json_body` is provided, it is forwarded using `json=json_body`
        so `httpx` encodes and sets the JSON content-type correctly.
      * Else (the usual case for JSON endpoints), the body is read once from
        the incoming `request`. If the Content-Type is JSON, the body is parsed
        into a Python object and forwarded as `json=...`. If parsing fails or
        the Content-Type is not JSON, the raw bytes are forwarded as
        `content=...`.

      This design ensures that in tests where `httpx.AsyncClient.request` is
      monkeypatched, `kwargs["json"]` correctly contains the payload for JSON
      endpoints like /v1/embeddings, /v1/images/generations, /v1/videos/generations,
      and /v1/responses. That matches how the official Python SDK uses `httpx`
      under the hood.

    - The upstream response’s status code, body, and content-type are mirrored
      back to the client, with hop-by-hop headers removed.

    Parameters
    ----------
    request:
        The FastAPI/Starlette Request instance for the inbound call.
    path:
        Optional explicit path (e.g. "/v1/embeddings"). If omitted, the
        incoming request.url.path is used.
    method:
        Optional explicit HTTP method. Defaults to request.method.
    raw_body:
        Optional raw bytes to forward as-is (e.g. multipart/form-data file
        uploads).
    json_body:
        Optional Python object to forward as JSON using `json=...`.
    content_type:
        Optional override for the Content-Type header when forwarding.

    Returns
    -------
    fastapi.responses.Response
        A Response mirroring the upstream OpenAI API call.
    """

    # -----------------------------------------------------------------------
    # 1) Determine path and method
    # -----------------------------------------------------------------------
    upstream_path = path or request.url.path
    upstream_method = (method or request.method).upper()

    base = OPENAI_API_BASE.rstrip("/")
    if upstream_path.startswith("/v1/"):
        upstream_url = f"{base}{upstream_path}"
    elif upstream_path.startswith("/"):
        upstream_url = f"{base}/v1{upstream_path}"
    else:
        upstream_url = f"{base}/v1/{upstream_path}"

    # -----------------------------------------------------------------------
    # 2) Build headers – copy from incoming, strip hop-by-hop and length
    # -----------------------------------------------------------------------
    headers: Dict[str, str] = {}
    for k, v in request.headers.items():
        kl = k.lower()
        if kl in HOP_BY_HOP_HEADERS or kl in {"host", "content-length"}:
            continue
        headers[k] = v

    # Force Authorization from env if provided, overriding inbound header
    if OPENAI_API_KEY:
        headers["Authorization"] = f"Bearer {OPENAI_API_KEY}"

    # Optional explicit content-type override
    if content_type:
        headers["Content-Type"] = content_type

    # -----------------------------------------------------------------------
    # 3) Query params – forwarded verbatim
    # -----------------------------------------------------------------------
    params = dict(request.query_params)

    logger.debug(
        "Forwarding to OpenAI: method=%s path=%s url=%s",
        upstream_method,
        upstream_path,
        upstream_url,
    )

    # -----------------------------------------------------------------------
    # 4) Perform upstream request using httpx
    # -----------------------------------------------------------------------
    async with httpx.AsyncClient(timeout=PROXY_TIMEOUT) as client:
        # Case 1: explicit raw_body for multipart / opaque content
        if raw_body is not None:
            upstream_response = await client.request(
                upstream_method,
                upstream_url,
                headers=headers,
                params=params,
                content=raw_body,
            )

        # Case 2: explicit Python object to send as JSON
        elif json_body is not None:
            upstream_response = await client.request(
                upstream_method,
                upstream_url,
                headers=headers,
                params=params,
                json=json_body,
            )

        # Case 3: derive JSON vs raw bytes from the inbound request
        else:
            body_bytes = await request.body()
            inbound_ct = (request.headers.get("content-type") or "").lower()

            json_payload: Any | None = None
            send_as_json = "application/json" in inbound_ct

            if send_as_json and body_bytes:
                try:
                    json_payload = json.loads(body_bytes.decode("utf-8"))
                except (ValueError, UnicodeDecodeError):
                    # If parsing fails, we fall back to raw content.
                    logger.debug(
                        "Failed to parse JSON body; falling back to raw content "
                        "for method=%s path=%s",
                        upstream_method,
                        upstream_path,
                    )
                    send_as_json = False

            if send_as_json and json_payload is not None:
                upstream_response = await client.request(
                    upstream_method,
                    upstream_url,
                    headers=headers,
                    params=params,
                    json=json_payload,
                )
            else:
                upstream_response = await client.request(
                    upstream_method,
                    upstream_url,
                    headers=headers,
                    params=params,
                    content=body_bytes,
                )

    logger.debug(
        "OpenAI upstream response: method=%s path=%s status=%s",
        upstream_method,
        upstream_path,
        upstream_response.status_code,
    )

    # -----------------------------------------------------------------------
    # 5) Build response to client – mirror status and relevant headers
    # -----------------------------------------------------------------------
    upstream_content_type = upstream_response.headers.get("content-type")
    response_headers: Dict[str, str] = {}

    for k, v in upstream_response.headers.items():
        kl = k.lower()
        if kl in HOP_BY_HOP_HEADERS or kl == "content-length":
            continue
        # Let FastAPI handle content-type separately
        if kl == "content-type":
            continue
        response_headers[k] = v

    return Response(
        content=upstream_response.content,
        status_code=upstream_response.status_code,
        media_type=upstream_content_type,
        headers=response_headers,
    )
