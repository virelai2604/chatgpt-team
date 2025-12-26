# app/api/images.py
from __future__ import annotations

import base64
import json
from typing import Any, Dict, List, Mapping, Optional, Tuple
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from starlette.responses import Response

from app.api.forward_openai import build_upstream_url, forward_openai_request
from app.core.config import get_settings
from app.utils.logger import relay_log as logger

router = APIRouter(prefix="/v1", tags=["images"])
actions_router = APIRouter(prefix="/v1/actions/images", tags=["images_actions"])

# SSRF hardening: allow only OpenAI-controlled download hosts.
_ALLOWED_HOSTS_EXACT: set[str] = {
    "files.openai.com",
}
_ALLOWED_HOST_SUFFIXES: Tuple[str, ...] = (
    "oaiusercontent.com",
    "openai.com",
    "openaiusercontent.com",
)
_ALLOWED_AZURE_BLOBS_PREFIXES: Tuple[str, ...] = (
    "oaidalle",
    "oaidalleapiprod",
)

_MAX_IMAGE_BYTES = 4 * 1024 * 1024  # 4MB
_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


class OpenAIFileIdRef(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    mime_type: Optional[str] = Field(default=None, alias="mime_type")
    download_link: Optional[str] = None


class ImagesVariationsJSON(BaseModel):
    # Primary Actions file input
    openaiFileIdRefs: Optional[List[OpenAIFileIdRef]] = None

    # Fallbacks
    image_url: Optional[str] = None
    image_base64: Optional[str] = None

    # Standard params
    model: Optional[str] = None
    n: Optional[int] = None
    size: Optional[str] = None
    response_format: Optional[str] = None
    user: Optional[str] = None


class ImagesEditsJSON(BaseModel):
    openaiFileIdRefs: Optional[List[OpenAIFileIdRef]] = None

    image_url: Optional[str] = None
    image_base64: Optional[str] = None
    mask_url: Optional[str] = None
    mask_base64: Optional[str] = None

    prompt: Optional[str] = None
    model: Optional[str] = None
    n: Optional[int] = None
    size: Optional[str] = None
    response_format: Optional[str] = None
    user: Optional[str] = None


def _is_multipart(request: Request) -> bool:
    ct = (request.headers.get("content-type") or "").lower()
    return ct.startswith("multipart/form-data")


def _validate_download_url(url: str) -> None:
    try:
        parsed = urlparse(url)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid URL: {exc}") from exc

    if parsed.scheme not in {"http", "https"}:
        raise HTTPException(status_code=400, detail="Only http/https URLs are supported")

    host = (parsed.hostname or "").lower()
    if not host:
        raise HTTPException(status_code=400, detail="Invalid URL host")

    if host in _ALLOWED_HOSTS_EXACT:
        return

    if any(host == s or host.endswith("." + s) for s in _ALLOWED_HOST_SUFFIXES):
        return

    # Allow specific OpenAI Azure blob hosts (tight pattern)
    if host.endswith("blob.core.windows.net") and any(host.startswith(p) for p in _ALLOWED_AZURE_BLOBS_PREFIXES):
        return

    raise HTTPException(status_code=400, detail="Refusing to fetch file URL from an untrusted host")


async def _download_bytes(url: str) -> bytes:
    _validate_download_url(url)

    timeout = httpx.Timeout(20.0, connect=10.0)
    limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)

    async with httpx.AsyncClient(timeout=timeout, limits=limits, follow_redirects=False) as client:
        async with client.stream("GET", url, headers={"Accept": "application/octet-stream"}) as resp:
            if resp.status_code != 200:
                raise HTTPException(status_code=400, detail=f"Failed to download file (HTTP {resp.status_code})")

            buf = bytearray()
            async for chunk in resp.aiter_bytes():
                buf.extend(chunk)
                if len(buf) > _MAX_IMAGE_BYTES:
                    raise HTTPException(status_code=400, detail="Image exceeds 4 MB limit")
            return bytes(buf)


def _ensure_png(data: bytes, *, label: str) -> None:
    if not data.startswith(_PNG_MAGIC):
        raise HTTPException(status_code=400, detail=f"Uploaded {label} must be a PNG")


def _as_str_form_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float, str)):
        return str(value)
    return json.dumps(value, separators=(",", ":"), ensure_ascii=False)


def _upstream_headers() -> Dict[str, str]:
    s = get_settings()
    headers: Dict[str, str] = {
        "Authorization": f"Bearer {s.OPENAI_API_KEY}",
        "Accept": "application/json",
        "Accept-Encoding": "identity",
    }
    if s.OPENAI_ORGANIZATION:
        headers["OpenAI-Organization"] = s.OPENAI_ORGANIZATION
    if s.OPENAI_PROJECT:
        headers["OpenAI-Project"] = s.OPENAI_PROJECT
    return headers


async def _post_multipart_to_upstream(
    *,
    endpoint_path: str,  # must include /v1/...
    files: Dict[str, Tuple[str, bytes, str]],
    data: Dict[str, str],
) -> Response:
    s = get_settings()
    upstream_url = build_upstream_url(endpoint_path)

    timeout = httpx.Timeout(60.0, connect=10.0)
    limits = httpx.Limits(max_keepalive_connections=10, max_connections=20)

    async with httpx.AsyncClient(timeout=timeout, limits=limits) as client:
        resp = await client.post(
            upstream_url,
            headers=_upstream_headers(),
            data=data,
            files=files,
        )

    content_type = resp.headers.get("content-type", "application/json")
    return Response(content=resp.content, status_code=resp.status_code, media_type=content_type)


async def _build_variations_multipart(payload: ImagesVariationsJSON) -> Tuple[Dict[str, Tuple[str, bytes, str]], Dict[str, str]]:
    image_bytes: Optional[bytes] = None
    image_name = "image.png"

    # Prefer Actions file refs
    if payload.openaiFileIdRefs:
        first = payload.openaiFileIdRefs[0]
        if not first.download_link:
            raise HTTPException(status_code=400, detail="openaiFileIdRefs[0].download_link is required")
        image_bytes = await _download_bytes(first.download_link)
        image_name = first.name or image_name

    # Fallbacks
    if image_bytes is None and payload.image_url:
        image_bytes = await _download_bytes(payload.image_url)

    if image_bytes is None and payload.image_base64:
        try:
            image_bytes = base64.b64decode(payload.image_base64, validate=True)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Invalid image_base64: {exc}") from exc

    if image_bytes is None:
        raise HTTPException(status_code=400, detail="Missing image input")

    _ensure_png(image_bytes, label="image")

    files = {"image": (image_name, image_bytes, "image/png")}

    form: Dict[str, str] = {}
    for k in ["model", "n", "size", "response_format", "user"]:
        v = getattr(payload, k)
        if v is not None:
            form[k] = _as_str_form_value(v)

    return files, form


async def _build_edits_multipart(payload: ImagesEditsJSON) -> Tuple[Dict[str, Tuple[str, bytes, str]], Dict[str, str]]:
    image_bytes: Optional[bytes] = None
    image_name = "image.png"

    mask_bytes: Optional[bytes] = None
    mask_name = "mask.png"

    if payload.openaiFileIdRefs:
        first = payload.openaiFileIdRefs[0]
        if not first.download_link:
            raise HTTPException(status_code=400, detail="openaiFileIdRefs[0].download_link is required")
        image_bytes = await _download_bytes(first.download_link)
        image_name = first.name or image_name

        if len(payload.openaiFileIdRefs) > 1:
            second = payload.openaiFileIdRefs[1]
            if second.download_link:
                mask_bytes = await _download_bytes(second.download_link)
                mask_name = second.name or mask_name

    if image_bytes is None and payload.image_url:
        image_bytes = await _download_bytes(payload.image_url)

    if image_bytes is None and payload.image_base64:
        try:
            image_bytes = base64.b64decode(payload.image_base64, validate=True)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Invalid image_base64: {exc}") from exc

    if image_bytes is None:
        raise HTTPException(status_code=400, detail="Missing image input")

    _ensure_png(image_bytes, label="image")

    if mask_bytes is None and payload.mask_url:
        mask_bytes = await _download_bytes(payload.mask_url)

    if mask_bytes is None and payload.mask_base64:
        try:
            mask_bytes = base64.b64decode(payload.mask_base64, validate=True)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Invalid mask_base64: {exc}") from exc

    if mask_bytes is not None:
        _ensure_png(mask_bytes, label="mask")

    files: Dict[str, Tuple[str, bytes, str]] = {"image": (image_name, image_bytes, "image/png")}
    if mask_bytes is not None:
        files["mask"] = (mask_name, mask_bytes, "image/png")

    form: Dict[str, str] = {}
    for k in ["prompt", "model", "n", "size", "response_format", "user"]:
        v = getattr(payload, k)
        if v is not None:
            form[k] = _as_str_form_value(v)

    return files, form


# --- Standard images routes ---


@router.post("/images", summary="Create image generation")
@router.post("/images/generations", summary="Create image generation (alias)")
async def create_image(request: Request) -> Response:
    logger.info("→ [images] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.post(
    "/images/variations",
    summary="Create image variations (multipart or JSON wrapper)",
    openapi_extra={
        "requestBody": {
            "content": {
                "application/json": {"schema": ImagesVariationsJSON.model_json_schema()},
            }
        }
    },
)
async def variations_image(request: Request) -> Response:
    logger.info("→ [images] %s %s", request.method, request.url.path)

    if _is_multipart(request):
        return await forward_openai_request(request)

    body = await request.json()
    payload = ImagesVariationsJSON.model_validate(body)
    files, form = await _build_variations_multipart(payload)
    return await _post_multipart_to_upstream(endpoint_path="/v1/images/variations", files=files, data=form)


@router.post(
    "/images/edits",
    summary="Edit an image (multipart or JSON wrapper)",
    openapi_extra={
        "requestBody": {
            "content": {
                "application/json": {"schema": ImagesEditsJSON.model_json_schema()},
            }
        }
    },
)
async def edit_image(request: Request) -> Response:
    logger.info("→ [images] %s %s", request.method, request.url.path)

    if _is_multipart(request):
        return await forward_openai_request(request)

    body = await request.json()
    payload = ImagesEditsJSON.model_validate(body)
    files, form = await _build_edits_multipart(payload)
    return await _post_multipart_to_upstream(endpoint_path="/v1/images/edits", files=files, data=form)


# --- Actions-friendly aliases with clean JSON schemas ---


@actions_router.post("/variations", summary="Actions JSON wrapper for image variations")
async def actions_variations(payload: ImagesVariationsJSON) -> Response:
    files, form = await _build_variations_multipart(payload)
    return await _post_multipart_to_upstream(endpoint_path="/v1/images/variations", files=files, data=form)


@actions_router.post("/edits", summary="Actions JSON wrapper for image edits")
async def actions_edits(payload: ImagesEditsJSON) -> Response:
    files, form = await _build_edits_multipart(payload)
    return await _post_multipart_to_upstream(endpoint_path="/v1/images/edits", files=files, data=form)
