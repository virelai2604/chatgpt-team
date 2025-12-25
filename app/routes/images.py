from __future__ import annotations

import base64
import json
from typing import Any, Mapping, MutableMapping, Optional
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, HTTPException, Request
from starlette.responses import Response

from app.api.forward_openai import forward_openai_request
from app.core.config import get_settings
from app.utils.logger import relay_log as logger

router = APIRouter(prefix="/v1", tags=["images"])

settings = get_settings()

# Conservative allowlist for GPT Action file URLs to reduce SSRF risk.
# OpenAI-hosted file links commonly use oaiusercontent.com; keep this list short and editable.
_ALLOWED_FILE_HOST_SUFFIXES: tuple[str, ...] = (
    "oaiusercontent.com",
    "openai.com",
    "openaiusercontent.com",
)

_MAX_IMAGE_BYTES = 4 * 1024 * 1024  # 4 MB
_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def _is_multipart(request: Request) -> bool:
    content_type = request.headers.get("content-type", "")
    return content_type.lower().startswith("multipart/form-data")


def _as_str_form_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float, str)):
        return str(value)
    # Lists/dicts: send JSON string so upstream can parse if supported.
    return json.dumps(value, separators=(",", ":"), ensure_ascii=False)


def _validate_download_url(url: str) -> None:
    try:
        parsed = urlparse(url)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid URL: {exc}") from exc

    if parsed.scheme not in {"https", "http"}:
        raise HTTPException(status_code=400, detail="Only http/https URLs are supported")

    host = (parsed.hostname or "").lower()
    if not host:
        raise HTTPException(status_code=400, detail="Invalid URL host")

    if not any(host == s or host.endswith("." + s) for s in _ALLOWED_FILE_HOST_SUFFIXES):
        raise HTTPException(
            status_code=400,
            detail="Refusing to fetch file URL from an untrusted host",
        )


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


def _ensure_png(data: bytes, *, label: str = "image") -> None:
    if not data.startswith(_PNG_MAGIC):
        raise HTTPException(status_code=400, detail=f"Uploaded {label} must be a PNG")


def _extract_openai_file_refs(body: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    """
    Actions file input is delivered as:
      openaiFileIdRefs: [{ id, name, mime_type, download_link }, ...]
    """
    refs = body.get("openaiFileIdRefs")
    if refs is None:
        return []
    if isinstance(refs, list):
        out: list[Mapping[str, Any]] = []
        for item in refs:
            if isinstance(item, dict):
                out.append(item)
            else:
                raise HTTPException(status_code=400, detail="openaiFileIdRefs must contain objects with download_link")
        return out
    raise HTTPException(status_code=400, detail="openaiFileIdRefs must be an array")


def _split_action_body(body: MutableMapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Separate file-ish fields from ordinary params."""
    file_fields: dict[str, Any] = {}
    params: dict[str, Any] = {}
    for k, v in body.items():
        if k in {
            "openaiFileIdRefs",
            "image_url",
            "mask_url",
            "image_base64",
            "image_b64",
            "mask_base64",
            "mask_b64",
        }:
            file_fields[k] = v
        else:
            params[k] = v
    return file_fields, params


async def _build_multipart_from_action_body(
    *,
    body: MutableMapping[str, Any],
    allow_mask: bool,
) -> tuple[dict[str, tuple[str, bytes, str]], dict[str, str]]:
    file_fields, params = _split_action_body(body)

    image_bytes: Optional[bytes] = None
    image_name = "image.png"

    mask_bytes: Optional[bytes] = None
    mask_name = "mask.png"

    refs = _extract_openai_file_refs(body)
    if refs:
        # Convention: first file is image; second file (optional) is mask.
        first = refs[0]
        url = first.get("download_link")
        if not isinstance(url, str) or not url:
            raise HTTPException(status_code=400, detail="openaiFileIdRefs[0].download_link is required")
        image_bytes = await _download_bytes(url)
        image_name = str(first.get("name") or image_name)

        if allow_mask and len(refs) > 1:
            second = refs[1]
            murl = second.get("download_link")
            if isinstance(murl, str) and murl:
                mask_bytes = await _download_bytes(murl)
                mask_name = str(second.get("name") or mask_name)

    # Fallbacks if openaiFileIdRefs not provided
    if image_bytes is None:
        if isinstance(file_fields.get("image_url"), str) and file_fields["image_url"]:
            image_bytes = await _download_bytes(file_fields["image_url"])
        elif isinstance(file_fields.get("image_base64"), str) and file_fields["image_base64"]:
            try:
                image_bytes = base64.b64decode(file_fields["image_base64"], validate=True)
            except Exception as exc:
                raise HTTPException(status_code=400, detail=f"Invalid image_base64: {exc}") from exc
        elif isinstance(file_fields.get("image_b64"), str) and file_fields["image_b64"]:
            try:
                image_bytes = base64.b64decode(file_fields["image_b64"], validate=True)
            except Exception as exc:
                raise HTTPException(status_code=400, detail=f"Invalid image_b64: {exc}") from exc

    if image_bytes is None:
        raise HTTPException(
            status_code=400,
            detail="Missing image input. Provide openaiFileIdRefs[0], image_url, or image_base64.",
        )

    _ensure_png(image_bytes, label="image")

    if allow_mask and mask_bytes is None:
        if isinstance(file_fields.get("mask_url"), str) and file_fields["mask_url"]:
            mask_bytes = await _download_bytes(file_fields["mask_url"])
        elif isinstance(file_fields.get("mask_base64"), str) and file_fields["mask_base64"]:
            try:
                mask_bytes = base64.b64decode(file_fields["mask_base64"], validate=True)
            except Exception as exc:
                raise HTTPException(status_code=400, detail=f"Invalid mask_base64: {exc}") from exc
        elif isinstance(file_fields.get("mask_b64"), str) and file_fields["mask_b64"]:
            try:
                mask_bytes = base64.b64decode(file_fields["mask_b64"], validate=True)
            except Exception as exc:
                raise HTTPException(status_code=400, detail=f"Invalid mask_b64: {exc}") from exc

    if mask_bytes is not None:
        _ensure_png(mask_bytes, label="mask")

    files: dict[str, tuple[str, bytes, str]] = {
        "image": (image_name, image_bytes, "image/png"),
    }
    if allow_mask and mask_bytes is not None:
        files["mask"] = (mask_name, mask_bytes, "image/png")

    form: dict[str, str] = {}
    for k, v in params.items():
        form[k] = _as_str_form_value(v)

    return files, form


def _upstream_headers_for_images() -> dict[str, str]:
    headers: dict[str, str] = {
        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
        "Accept": "application/json",
        "Accept-Encoding": "identity",
    }
    if getattr(settings, "OPENAI_ORG", None):
        headers["OpenAI-Organization"] = settings.OPENAI_ORG
    if getattr(settings, "OPENAI_PROJECT", None):
        headers["OpenAI-Project"] = settings.OPENAI_PROJECT
    return headers


async def _post_images_multipart_to_upstream(
    *,
    endpoint: str,
    files: dict[str, tuple[str, bytes, str]],
    data: dict[str, str],
) -> Response:
    upstream_url = settings.OPENAI_API_BASE.rstrip("/") + endpoint
    timeout = httpx.Timeout(60.0, connect=10.0)
    limits = httpx.Limits(max_keepalive_connections=10, max_connections=20)

    async with httpx.AsyncClient(timeout=timeout, limits=limits) as client:
        resp = await client.post(
            upstream_url,
            headers=_upstream_headers_for_images(),
            data=data,
            files=files,
        )

    content_type = resp.headers.get("content-type", "application/json")
    return Response(content=resp.content, status_code=resp.status_code, media_type=content_type)


@router.post("/images", summary="Create image generation")
@router.post("/images/generations", summary="Create image generation (alias)")
async def create_image(request: Request) -> Response:
    logger.info("→ [images] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.post("/images/edits", summary="Edit an image (multipart or Actions JSON)")
async def edit_image(request: Request) -> Response:
    logger.info("→ [images] %s %s (edits)", request.method, request.url.path)

    if _is_multipart(request):
        return await forward_openai_request(request)

    # Actions-friendly JSON wrapper -> server-side multipart to upstream
    body = await request.json()
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="Body must be a JSON object")

    files, form = await _build_multipart_from_action_body(body=body, allow_mask=True)
    return await _post_images_multipart_to_upstream(endpoint="/images/edits", files=files, data=form)


@router.post("/images/variations", summary="Create image variations (multipart or Actions JSON)")
async def variations_image(request: Request) -> Response:
    logger.info("→ [images] %s %s (variations)", request.method, request.url.path)

    if _is_multipart(request):
        return await forward_openai_request(request)

    body = await request.json()
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="Body must be a JSON object")

    files, form = await _build_multipart_from_action_body(body=body, allow_mask=False)
    return await _post_images_multipart_to_upstream(endpoint="/images/variations", files=files, data=form)
