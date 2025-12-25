from __future__ import annotations

import base64
import binascii
import ipaddress
from typing import Any, Optional
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette.responses import Response

from app.api.forward_openai import (
    build_outbound_headers,
    build_upstream_url,
    filter_upstream_headers,
    forward_openai_request,
)
from app.core.config import get_settings
from app.core.http_client import get_async_httpx_client
from app.models.error import ErrorResponse
from app.utils.logger import relay_log as logger

router = APIRouter(prefix="/v1", tags=["images"])

_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
_MAX_PNG_BYTES = 4 * 1024 * 1024  # 4 MiB (matches upstream constraint)


# ---------------------------------------------------------------------------
# Direct OpenAI-compatible endpoints (multipart)
# ---------------------------------------------------------------------------

@router.post("/images", summary="Create image generation")
@router.post("/images/generations", summary="Create image generation (alias)")
async def create_image(request: Request) -> Response:
    logger.info("→ [images] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.post("/images/edits", summary="Edit an image (multipart)")
async def edit_image(request: Request) -> Response:
    logger.info("→ [images] %s %s (edits)", request.method, request.url.path)
    return await forward_openai_request(request)


@router.post("/images/variations", summary="Create image variations (multipart)")
async def variations_image(request: Request) -> Response:
    logger.info("→ [images] %s %s (variations)", request.method, request.url.path)
    return await forward_openai_request(request)


# ---------------------------------------------------------------------------
# Actions-friendly wrappers (JSON body with file URLs/base64)
# ---------------------------------------------------------------------------

class ActionImageVariationsRequest(BaseModel):
    image_url: Optional[str] = Field(
        default=None,
        description="HTTPS URL to a PNG image (ChatGPT Actions file_url mode).",
    )
    image_base64: Optional[str] = Field(
        default=None,
        description="Base64-encoded PNG bytes (optionally a data: URL).",
    )
    model: Optional[str] = Field(default=None, description="Optional upstream model parameter (if supported).")
    n: Optional[int] = Field(default=1, ge=1, le=10)
    size: Optional[str] = Field(default=None, description="e.g. 256x256, 512x512, 1024x1024")
    response_format: Optional[str] = Field(default=None, description="url or b64_json")
    user: Optional[str] = Field(default=None)


class ActionImageEditsRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    image_url: Optional[str] = Field(default=None, description="HTTPS URL to a PNG image.")
    image_base64: Optional[str] = Field(default=None, description="Base64-encoded PNG bytes (optionally a data: URL).")
    mask_url: Optional[str] = Field(default=None, description="HTTPS URL to a PNG mask image.")
    mask_base64: Optional[str] = Field(default=None, description="Base64-encoded PNG mask bytes (optionally a data: URL).")
    model: Optional[str] = Field(default=None, description="Optional upstream model parameter (if supported).")
    n: Optional[int] = Field(default=1, ge=1, le=10)
    size: Optional[str] = Field(default=None, description="e.g. 256x256, 512x512, 1024x1024")
    response_format: Optional[str] = Field(default=None, description="url or b64_json")
    user: Optional[str] = Field(default=None)


def _error(status_code: int, message: str, code: str | None = None, param: str | None = None) -> JSONResponse:
    payload = ErrorResponse(
        error={
            "message": message,
            "type": "invalid_request_error",
            "param": param,
            "code": code,
        }
    )
    return JSONResponse(status_code=status_code, content=payload.model_dump())


def _strip_data_url_prefix(b64: str) -> str:
    # Accept: data:image/png;base64,XXXX
    prefix = "data:image/png;base64,"
    if b64.startswith(prefix):
        return b64[len(prefix) :]
    return b64


def _looks_like_png(data: bytes) -> bool:
    return len(data) >= len(_PNG_SIGNATURE) and data.startswith(_PNG_SIGNATURE)


def _validate_https_url(url: str) -> tuple[bool, str]:
    try:
        parsed = urlparse(url)
    except Exception:
        return False, "Invalid URL."

    if parsed.scheme.lower() != "https":
        return False, "Only https:// URLs are allowed."

    if not parsed.netloc:
        return False, "URL must include a hostname."

    hostname = (parsed.hostname or "").strip().lower()
    if not hostname:
        return False, "URL must include a hostname."

    # Obvious SSRF targets
    if hostname in {"localhost", "127.0.0.1", "0.0.0.0", "::1"}:
        return False, "Localhost URLs are not allowed."

    # Block private / link-local / reserved IP literals
    try:
        ip = ipaddress.ip_address(hostname)
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
            or ip.is_unspecified
        ):
            return False, "Private or non-routable IPs are not allowed."
    except ValueError:
        # hostname is not an IP literal; allow (DNS resolution happens in the HTTP client)
        pass

    # Optional: restrict unusual ports (Actions file URLs are typically 443)
    if parsed.port not in (None, 443):
        return False, "Only the default HTTPS port (443) is allowed."

    return True, ""


async def _download_png(url: str) -> bytes:
    ok, reason = _validate_https_url(url)
    if not ok:
        raise ValueError(reason)

    # Dedicated client with NO OpenAI auth headers to avoid key leakage.
    timeout = httpx.Timeout(connect=10.0, read=30.0, write=30.0, pool=10.0)
    async with httpx.AsyncClient(
        timeout=timeout,
        follow_redirects=True,
        headers={"User-Agent": "chatgpt-team-relay/0.1.0"},
    ) as client:
        buf = bytearray()
        async with client.stream("GET", url) as resp:
            # Re-validate final URL after redirects.
            ok, reason = _validate_https_url(str(resp.url))
            if not ok:
                raise ValueError(f"Redirected to an unsafe URL: {reason}")

            if resp.status_code >= 400:
                raise ValueError(f"Failed to download image (HTTP {resp.status_code}).")

            async for chunk in resp.aiter_bytes():
                if not chunk:
                    continue
                buf.extend(chunk)
                if len(buf) > _MAX_PNG_BYTES:
                    raise ValueError("Image is too large (max 4MB).")

    data = bytes(buf)
    if not _looks_like_png(data):
        raise ValueError("Downloaded file is not a PNG.")

    return data


def _decode_png_base64(b64: str) -> bytes:
    b64 = _strip_data_url_prefix(b64.strip())
    try:
        raw = base64.b64decode(b64, validate=True)
    except (binascii.Error, ValueError):
        raise ValueError("Invalid base64 payload.") from None

    if len(raw) > _MAX_PNG_BYTES:
        raise ValueError("Image is too large (max 4MB).")

    if not _looks_like_png(raw):
        raise ValueError("Decoded file is not a PNG.")

    return raw


async def _get_png_bytes(url: Optional[str], b64: Optional[str], param_name: str) -> bytes:
    if bool(url) == bool(b64):
        raise ValueError(f"Provide exactly one of {param_name}_url or {param_name}_base64.")
    if url:
        return await _download_png(url)
    return _decode_png_base64(b64 or "")


async def _post_upstream_multipart(request: Request, upstream_path: str, *, files: dict[str, Any], data: dict[str, Any]) -> Response:
    s = get_settings()
    upstream_url = build_upstream_url(s, upstream_path)
    headers = build_outbound_headers(
        request.headers,
        accept="application/json",
        forward_accept=False,
        content_type=None,  # let httpx set multipart boundary
    )

    client = get_async_httpx_client()
    upstream_resp = await client.post(
        upstream_url,
        headers=headers,
        data=data,
        files=files,
    )

    return Response(
        content=upstream_resp.content,
        status_code=upstream_resp.status_code,
        headers=filter_upstream_headers(upstream_resp.headers),
        media_type=upstream_resp.headers.get("content-type"),
    )


@router.post("/actions/images/variations", summary="Create image variations (Actions JSON wrapper)")
async def actions_image_variations(payload: ActionImageVariationsRequest, request: Request) -> Response:
    """Actions wrapper for /v1/images/variations.

    Accepts file URLs / base64 and performs the required multipart upload server-side.
    """
    logger.info("→ [images/actions] POST %s", request.url.path)

    try:
        image_bytes = await _get_png_bytes(payload.image_url, payload.image_base64, "image")
    except ValueError as e:
        return _error(400, str(e), param="image")

    files = {"image": ("image.png", image_bytes, "image/png")}
    data: dict[str, Any] = {}

    if payload.n is not None:
        data["n"] = str(payload.n)
    if payload.size:
        data["size"] = payload.size
    if payload.response_format:
        data["response_format"] = payload.response_format
    if payload.model:
        data["model"] = payload.model
    if payload.user:
        data["user"] = payload.user

    return await _post_upstream_multipart(request, "/v1/images/variations", files=files, data=data)


@router.post("/actions/images/edits", summary="Edit an image (Actions JSON wrapper)")
async def actions_image_edits(payload: ActionImageEditsRequest, request: Request) -> Response:
    """Actions wrapper for /v1/images/edits.

    Accepts file URLs / base64 and performs the required multipart upload server-side.
    """
    logger.info("→ [images/actions] POST %s", request.url.path)

    try:
        image_bytes = await _get_png_bytes(payload.image_url, payload.image_base64, "image")
    except ValueError as e:
        return _error(400, str(e), param="image")

    mask_bytes: Optional[bytes] = None
    if payload.mask_url or payload.mask_base64:
        try:
            mask_bytes = await _get_png_bytes(payload.mask_url, payload.mask_base64, "mask")
        except ValueError as e:
            return _error(400, str(e), param="mask")

    files = {"image": ("image.png", image_bytes, "image/png")}
    if mask_bytes is not None:
        files["mask"] = ("mask.png", mask_bytes, "image/png")

    data: dict[str, Any] = {"prompt": payload.prompt}

    if payload.n is not None:
        data["n"] = str(payload.n)
    if payload.size:
        data["size"] = payload.size
    if payload.response_format:
        data["response_format"] = payload.response_format
    if payload.model:
        data["model"] = payload.model
    if payload.user:
        data["user"] = payload.user

    return await _post_upstream_multipart(request, "/v1/images/edits", files=files, data=data)
