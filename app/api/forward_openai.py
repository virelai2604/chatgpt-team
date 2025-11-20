# app/api/forward_openai.py

from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional

import httpx
from fastapi import Request, UploadFile
from fastapi.responses import JSONResponse, Response

from app.utils.logger import get_logger

logger = get_logger(__name__)

OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_ORG_ID = os.getenv("OPENAI_ORG_ID")
OPENAI_PROJECT_ID = os.getenv("OPENAI_PROJECT_ID")
RELAY_TIMEOUT = float(os.getenv("RELAY_TIMEOUT", "120"))


def _build_upstream_url(upstream_path: str) -> str:
    """
    Build a correct OpenAI URL, avoiding double /v1 or missing /v1.
    upstream_path is expected like "/files", "/responses", "/files/{id}/content", etc.
    """
    base = OPENAI_API_BASE.rstrip("/")
    if not upstream_path.startswith("/"):
        upstream_path = "/" + upstream_path

    # If base already ends with /v1, don't add another /v1
    if base.endswith("/v1"):
        return f"{base}{upstream_path}"

    return f"{base}/v1{upstream_path}"


def _filter_response_headers(headers: httpx.Headers) -> Dict[str, str]:
    """
    Strip hop-by-hop headers that should not be forwarded back to the client.
    """
    excluded = {
        "connection",
        "keep-alive",
        "proxy-authenticate",
        "proxy-authorization",
        "te",
        "trailers",
        "transfer-encoding",
        "upgrade",
        "content-encoding",
    }
    filtered: Dict[str, str] = {}
    for key, value in headers.items():
        if key.lower() in excluded:
            continue
        filtered[key] = value
    return filtered


def _build_upstream_headers(request: Request, content_type: Optional[str]) -> Dict[str, str]:
    """
    Construct a clean headers set for OpenAI, based on env + selected
    pass-through headers from the incoming request.
    """
    if not OPENAI_API_KEY:
        # This will be handled by forward_* functions, but keep it defensive.
        raise RuntimeError("OPENAI_API_KEY is not configured")

    headers: Dict[str, str] = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
    }

    # Honor client Accept when present (for JSON vs SSE, etc.)
    accept = request.headers.get("accept")
    if accept:
        headers["Accept"] = accept

    # Optional org/project routing
    if OPENAI_ORG_ID:
        headers.setdefault("OpenAI-Organization", OPENAI_ORG_ID)
    if OPENAI_PROJECT_ID:
        headers.setdefault("OpenAI-Project", OPENAI_PROJECT_ID)

    # Pass-through feature flags / betas
    beta = request.headers.get("OpenAI-Beta")
    if beta:
        headers["OpenAI-Beta"] = beta

    # Content-Type handling:
    if content_type:
        headers["Content-Type"] = content_type
    else:
        incoming_ct = request.headers.get("content-type")
        if incoming_ct:
            headers["Content-Type"] = incoming_ct

    return headers


async def forward_openai_request(
    request: Request,
    upstream_path: str,
    method: str,
    raw_body: Optional[bytes] = None,
    content_type: Optional[str] = None,
    stream_binary: bool = False,
) -> Response:
    """
    Generic forwarder used by most JSON-style OpenAI endpoints.
    - upstream_path: path *after* /v1 (e.g. "/files", "/responses")
    - method: HTTP verb ("GET", "POST", "DELETE", ...)
    - raw_body: optional pre-read body (for cases like /v1/responses)
    - content_type: optional explicit content-type override
    - stream_binary: if True, return raw bytes (e.g. file content download)
    """
    if not OPENAI_API_KEY:
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "message": "OPENAI_API_KEY is not configured on the relay.",
                    "type": "relay_config_error",
                }
            },
        )

    url = _build_upstream_url(upstream_path)
    method = method.upper()

    headers = _build_upstream_headers(request, content_type)
    timeout = httpx.Timeout(RELAY_TIMEOUT)

    body: Optional[bytes] = raw_body
    if body is None and method in ("POST", "PATCH", "PUT"):
        body = await request.body()

    logger.debug(
        "Forwarding request to OpenAI",
        extra={
            "method": method,
            "url": url,
            "stream_binary": stream_binary,
        },
    )

    async with httpx.AsyncClient(timeout=timeout) as client:
        upstream_resp = await client.request(
            method=method,
            url=url,
            headers=headers,
            content=body,
        )

    media_type = upstream_resp.headers.get("content-type", "")

    # For binary streams (e.g. file content), just mirror bytes back.
    if stream_binary and upstream_resp.content is not None:
        return Response(
            content=upstream_resp.content,
            status_code=upstream_resp.status_code,
            headers=_filter_response_headers(upstream_resp.headers),
            media_type=media_type or None,
        )

    # Prefer JSON for normal API calls
    if "application/json" in media_type:
        try:
            data: Any = upstream_resp.json()
        except json.JSONDecodeError:
            # Fallback – send raw body with JSON content-type
            return Response(
                content=upstream_resp.content,
                status_code=upstream_resp.status_code,
                headers=_filter_response_headers(upstream_resp.headers),
                media_type=media_type or "application/json",
            )

        return JSONResponse(
            status_code=upstream_resp.status_code,
            content=data,
            headers=_filter_response_headers(upstream_resp.headers),
        )

    # Non-JSON content: just return as-is
    return Response(
        content=upstream_resp.content,
        status_code=upstream_resp.status_code,
        headers=_filter_response_headers(upstream_resp.headers),
        media_type=media_type or None,
    )


async def forward_multipart_to_openai(
    request: Request,
    upstream_path: str,
    file: UploadFile,
    purpose: str,
) -> Response:
    """
    Special-case forwarder for POST /v1/files with multipart/form-data.

    We reconstruct the upload using httpx's 'files' + 'data' interface so
    that it is indistinguishable from the direct OpenAI curl example.
    """
    if not OPENAI_API_KEY:
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "message": "OPENAI_API_KEY is not configured on the relay.",
                    "type": "relay_config_error",
                }
            },
        )

    url = _build_upstream_url(upstream_path)
    headers = _build_upstream_headers(request, content_type=None)

    # NOTE: do NOT set Content-Type manually here; httpx will set the multipart
    # boundary correctly when we pass 'files=' below.
    headers.pop("Content-Type", None)

    timeout = httpx.Timeout(RELAY_TIMEOUT)

    file_bytes = await file.read()
    filename = file.filename or "upload.bin"
    file_ct = file.content_type or "application/octet-stream"

    files_param = {
        "file": (filename, file_bytes, file_ct),
    }
    data_param = {
        "purpose": purpose,
    }

    logger.debug(
        "Forwarding multipart upload to OpenAI",
        extra={
            "url": url,
            "filename": filename,
            "purpose": purpose,
        },
    )

    async with httpx.AsyncClient(timeout=timeout) as client:
        upstream_resp = await client.post(
            url,
            headers=headers,
            data=data_param,
            files=files_param,
        )

    media_type = upstream_resp.headers.get("content-type", "")

    if "application/json" in media_type:
        try:
            payload: Any = upstream_resp.json()
        except json.JSONDecodeError:
            return Response(
                content=upstream_resp.content,
                status_code=upstream_resp.status_code,
                headers=_filter_response_headers(upstream_resp.headers),
                media_type=media_type or "application/json",
            )

        return JSONResponse(
            status_code=upstream_resp.status_code,
            content=payload,
            headers=_filter_response_headers(upstream_resp.headers),
        )

    return Response(
        content=upstream_resp.content,
        status_code=upstream_resp.status_code,
        headers=_filter_response_headers(upstream_resp.headers),
        media_type=media_type or None,
    )
