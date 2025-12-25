from __future__ import annotations

import base64
import binascii
import ipaddress
from typing import Dict, Optional, Tuple
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from starlette.responses import Response

from app.api.forward_openai import build_upstream_url, forward_openai_request
from app.core.config import settings
from app.core.http_client import get_async_httpx_client
from app.utils.logger import relay_log as logger

router = APIRouter(prefix="/v1", tags=["images"])

# Hard safety limit for server-side URL/base64 ingestion (Actions wrapper endpoints).
# This is NOT an OpenAI limit; it's a relay safety limit to avoid large downloads/memory spikes.
_MAX_ACTION_INPUT_BYTES = 10 * 1024 * 1024  # 10 MiB


def _bad_request(detail: str) -> None:
    raise HTTPException(status_code=400, detail=detail)


def _validate_fetch_url(url: str) -> None:
    """
    Minimal SSRF guard for Actions wrapper endpoints.

    Assumptions:
      - Actions provide HTTPS file URLs (common for ChatGPT file URL model).
      - We explicitly refuse localhost / private IP literals.
      - We do not perform DNS resolution here (to keep this lightweight).
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("https",):
        _bad_request("Only https:// URLs are allowed for Actions image wrappers.")

    host = (parsed.hostname or "").strip()
    if not host:
        _bad_request("Invalid URL.")

    host_l = host.lower()
    if host_l in {"localhost"} or host_l.endswith(".local"):
        _bad_request("Refusing to fetch from local hostnames.")

    # If hostname is a literal IP address, block private/reserved ranges.
    try:
        ip = ipaddress.ip_address(host_l)
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
            or ip.is_unspecified
        ):
            _bad_request("Refusing to fetch from private or local network addresses.")
    except ValueError:
        # Not a literal IP; could still resolve to one, but we avoid DNS resolution here.
        pass


async def _fetch_bytes(url: str) -> Tuple[bytes, str]:
    _validate_fetch_url(url)
    client = get_async_httpx_client()

    try:
        r = await client.get(url, follow_redirects=True)
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch URL: {e}") from e

    if r.status_code >= 400:
        raise HTTPException(status_code=502, detail=f"Failed to fetch URL (HTTP {r.status_code}).")

    blob = r.content
    if len(blob) > _MAX_ACTION_INPUT_BYTES:
        _bad_request(f"Fetched object too large ({len(blob)} bytes).")

    content_type = (r.headers.get("content-type") or "application/octet-stream").split(";", 1)[0].strip()
    return blob, content_type


def _decode_base64(data_b64: str) -> bytes:
    # Accept both raw base64 and data: URLs.
    if data_b64.startswith("data:"):
        try:
            _, b64_part = data_b64.split(",", 1)
        except ValueError:
            _bad_request("Invalid data: URL for base64 payload.")
        data_b64 = b64_part

    try:
        blob = base64.b64decode(data_b64, validate=True)
    except (binascii.Error, ValueError) as e:
        _bad_request(f"Invalid base64 payload: {e}")

    if len(blob) > _MAX_ACTION_INPUT_BYTES:
        _bad_request(f"Decoded object too large ({len(blob)} bytes).")

    return blob


async def _resolve_blob(*, url: Optional[str], b64: Optional[str], label: str) -> Tuple[bytes, str]:
    """
    Resolve a binary blob either from a URL fetch or a base64 payload.
    Returns: (bytes, content_type)
    """
    if bool(url) == bool(b64):
        _bad_request(f"Provide exactly one of {label}_url or {label}_base64.")

    if url:
        blob, content_type = await _fetch_bytes(url)
        return blob, content_type

    assert b64 is not None
    # Default to PNG when the client didn't send an explicit MIME type.
    return _decode_base64(b64), "image/png"


def _coerce_multipart_data(d: Dict[str, object]) -> Dict[str, str]:
    """httpx multipart 'data=' fields must be string-ish."""
    out: Dict[str, str] = {}
    for k, v in d.items():
        if v is None:
            continue
        out[k] = str(v)
    return out


def _pydantic_dump(model: BaseModel) -> Dict[str, object]:
    # Pydantic v2 uses model_dump; v1 uses dict.
    if hasattr(model, "model_dump"):
        return model.model_dump(exclude_none=True)  # type: ignore[no-any-return]
    return model.dict(exclude_none=True)  # type: ignore[no-any-return]


def _upstream_headers(request: Request) -> Dict[str, str]:
    """
    Build upstream headers for server-to-server wrapper calls.
    We intentionally do NOT forward relay auth headers (X-Relay-Key).
    """
    headers: Dict[str, str] = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Accept": "application/json",
    }

    # Optional org/project overrides if your clients set them.
    for h in ("OpenAI-Organization", "OpenAI-Project", "OpenAI-Beta"):
        v = request.headers.get(h)
        if v:
            headers[h] = v

    return headers


def _response_from_upstream(r: httpx.Response) -> Response:
    media_type = (r.headers.get("content-type") or "application/octet-stream").split(";", 1)[0].strip()

    passthrough_headers: Dict[str, str] = {}
    for h in ("x-request-id", "openai-request-id"):
        v = r.headers.get(h)
        if v:
            passthrough_headers[h] = v

    return Response(
        content=r.content,
        status_code=r.status_code,
        headers=passthrough_headers,
        media_type=media_type,
    )


# ---------------------------------------------------------------------------
# Standard OpenAI-compatible image routes (pass-through)
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
# Actions-friendly wrappers (JSON in, relay builds multipart upstream)
# ---------------------------------------------------------------------------

class ActionImageEditRequest(BaseModel):
    # Standard OpenAI fields
    prompt: str = Field(..., description="Text prompt describing the desired edit.")
    model: Optional[str] = Field(default=None, description="Image model (e.g., gpt-image-1, dall-e-2).")
    n: Optional[int] = Field(default=None, ge=1, le=10)
    size: Optional[str] = None
    response_format: Optional[str] = None
    user: Optional[str] = None

    # Actions-friendly image inputs
    image_url: Optional[str] = Field(default=None, description="HTTPS URL to the base image.")
    image_base64: Optional[str] = Field(default=None, description="Base64 (or data: URL) for the base image.")
    mask_url: Optional[str] = Field(default=None, description="HTTPS URL to the mask image (optional).")
    mask_base64: Optional[str] = Field(default=None, description="Base64 (or data: URL) for the mask (optional).")

    # Optional filenames (cosmetic)
    image_filename: str = "image.png"
    mask_filename: str = "mask.png"


class ActionImageVariationRequest(BaseModel):
    model: Optional[str] = None
    n: Optional[int] = Field(default=None, ge=1, le=10)
    size: Optional[str] = None
    response_format: Optional[str] = None
    user: Optional[str] = None

    image_url: Optional[str] = None
    image_base64: Optional[str] = None
    image_filename: str = "image.png"


@router.post(
    "/actions/images/edits",
    summary="Actions-friendly image edit (JSON url/base64 → multipart upstream)",
)
async def actions_image_edits(payload: ActionImageEditRequest, request: Request) -> Response:
    logger.info("→ [actions/images] %s %s", request.method, request.url.path)

    image_bytes, image_ct = await _resolve_blob(url=payload.image_url, b64=payload.image_base64, label="image")
    if not image_ct.startswith("image/"):
        _bad_request(f"image must be an image/* content-type (got {image_ct}).")

    mask_bytes: Optional[bytes] = None
    mask_ct: Optional[str] = None
    if payload.mask_url or payload.mask_base64:
        mask_bytes, mask_ct = await _resolve_blob(url=payload.mask_url, b64=payload.mask_base64, label="mask")
        if not mask_ct.startswith("image/"):
            _bad_request(f"mask must be an image/* content-type (got {mask_ct}).")

    data_obj = _pydantic_dump(payload)

    # Remove wrapper-only fields before sending upstream.
    for k in (
        "image_url",
        "image_base64",
        "mask_url",
        "mask_base64",
        "image_filename",
        "mask_filename",
    ):
        data_obj.pop(k, None)

    files: Dict[str, tuple[str, bytes, str]] = {
        "image": (payload.image_filename, image_bytes, image_ct),
    }
    if mask_bytes is not None and mask_ct is not None:
        files["mask"] = (payload.mask_filename, mask_bytes, mask_ct)

    upstream_url = build_upstream_url("/v1/images/edits")
    client = get_async_httpx_client()

    r = await client.post(
        upstream_url,
        headers=_upstream_headers(request),
        data=_coerce_multipart_data(data_obj),
        files=files,
    )
    return _response_from_upstream(r)


@router.post(
    "/actions/images/variations",
    summary="Actions-friendly image variations (JSON url/base64 → multipart upstream)",
)
async def actions_image_variations(payload: ActionImageVariationRequest, request: Request) -> Response:
    logger.info("→ [actions/images] %s %s", request.method, request.url.path)

    image_bytes, image_ct = await _resolve_blob(url=payload.image_url, b64=payload.image_base64, label="image")
    if not image_ct.startswith("image/"):
        _bad_request(f"image must be an image/* content-type (got {image_ct}).")

    data_obj = _pydantic_dump(payload)

    for k in ("image_url", "image_base64", "image_filename"):
        data_obj.pop(k, None)

    files: Dict[str, tuple[str, bytes, str]] = {
        "image": (payload.image_filename, image_bytes, image_ct),
    }

    upstream_url = build_upstream_url("/v1/images/variations")
    client = get_async_httpx_client()

    r = await client.post(
        upstream_url,
        headers=_upstream_headers(request),
        data=_coerce_multipart_data(data_obj),
        files=files,
    )
    return _response_from_upstream(r)
