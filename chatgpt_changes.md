# ChatGPT Sync
Repo: chatgpt-team
Base: origin/main
Base commit (merge-base): 6d3237a6535e0cf1c039ec4706236692584ef89b
Dirs: app tests static schemas src scripts/src
Root files: project-tree.md pyproject.toml chatgpt_sync.sh AGENTS.md __init__.py generate_tree.py
Mode: changes
Generated: 2025-12-25T14:50:36+07:00

## CHANGE SUMMARY (since 6d3237a6535e0cf1c039ec4706236692584ef89b, includes worktree)

```
M	app/api/tools_api.py
M	app/routes/images.py
M	project-tree.md
D	tests/test_images_variations_integration - Copy.py
```

## PATCH (since 6d3237a6535e0cf1c039ec4706236692584ef89b, includes worktree)

```diff
diff --git a/app/api/tools_api.py b/app/api/tools_api.py
index 1e6947f..90523aa 100755
--- a/app/api/tools_api.py
+++ b/app/api/tools_api.py
@@ -1,147 +1,93 @@
-# ==========================================================
-# app/api/tools_api.py — Tools Manifest Endpoints
-# ==========================================================
-"""
-Serves the relay's tools manifest at:
-  - GET /manifest
-  - GET /v1/manifest
-
-Intent:
-  - Option A (Actions-friendly): expose a small, JSON-only tool surface.
-  - Full route inventory lives in OpenAPI at /openapi.json.
-
-The integration tests expect:
-  data["endpoints"]["responses"] includes "/v1/responses"
-  data["endpoints"]["responses_compact"] includes "/v1/responses/compact"
-"""
-
 from __future__ import annotations
 
-import json
-import logging
-from datetime import datetime, timezone
-from pathlib import Path
-from typing import Any, Dict, List, Optional, Union, cast
-
-from fastapi import APIRouter
-
-from ..core.config import get_settings
+import copy
+from typing import Any
 
-logger = logging.getLogger(__name__)
+from fastapi import APIRouter, Request
+from fastapi.responses import JSONResponse
 
-router = APIRouter(tags=["manifest"])
+from app.core.config import settings
 
+# This router serves:
+#   - /manifest: a lightweight capability manifest for human/dev tooling
+#   - /openapi.actions.json: a curated OpenAPI subset suitable for ChatGPT Actions
 
-def _read_json(path: Path) -> Any:
-    with path.open("r", encoding="utf-8") as f:
-        return json.load(f)
+router = APIRouter()
 
-
-def _extract_tools(payload: Any) -> List[Dict[str, Any]]:
-    """
-    Accept multiple on-disk shapes safely:
-      - {"tools": [...]}                       (legacy)
-      - {"data": [...], "object": "list", ...} (what /manifest returns)
-      - [...]                                   (raw list of tool dicts)
+MANIFEST: dict[str, Any] = {
+    "object": "relay.manifest",
+    "data": [],
+    "endpoints": {
+        "health": ["/health", "/v1/health"],
+        "models": ["/v1/models", "/v1/models/{model}"],
+        "responses": ["/v1/responses", "/v1/responses/compact"],
+        "embeddings": ["/v1/embeddings"],
+        "images": ["/v1/images/generations"],
+        "images_actions": ["/v1/actions/images/variations", "/v1/actions/images/edits"],
+        "files": ["/v1/files", "/v1/files/{file_id}", "/v1/files/{file_id}/content"],
+        "uploads": [
+            "/v1/uploads",
+            "/v1/uploads/{upload_id}",
+            "/v1/uploads/{upload_id}/parts",
+            "/v1/uploads/{upload_id}/complete",
+            "/v1/uploads/{upload_id}/cancel",
+        ],
+        "batches": ["/v1/batches", "/v1/batches/{batch_id}"],
+        "proxy": ["/v1/proxy"],
+    },
+    "meta": {
+        "relay_name": "chatgpt-team relay",
+        "auth_required": settings.RELAY_AUTH_ENABLED,
+        "auth_header": "X-Relay-Key",
+        "upstream_base_url": settings.UPSTREAM_BASE_URL,
+        "actions_openapi_url": "/openapi.actions.json",
+        "actions_openapi_groups": [
+            "health",
+            "models",
+            "responses",
+            "embeddings",
+            "images",
+            "images_actions",
+            "proxy",
+        ],
+    },
+}
+
+
+@router.get("/manifest", include_in_schema=False)
+@router.get("/v1/manifest", include_in_schema=False)
+async def get_manifest() -> dict[str, Any]:
+    return MANIFEST
+
+
+@router.get("/openapi.actions.json", include_in_schema=False)
+async def openapi_actions(request: Request) -> JSONResponse:
     """
-    if isinstance(payload, list):
-        return cast(List[Dict[str, Any]], payload)
-
-    if isinstance(payload, dict):
-        tools = payload.get("tools")
-        if isinstance(tools, list):
-            return cast(List[Dict[str, Any]], tools)
-
-        data = payload.get("data")
-        if isinstance(data, list):
-            return cast(List[Dict[str, Any]], data)
-
-    return []
+    Return an Actions-safe OpenAPI schema.
 
-
-def load_tools_manifest() -> List[Dict[str, Any]]:
-    """
-    Loads tools from:
-      1) settings.TOOLS_MANIFEST (if it's a list of tools)
-      2) settings.TOOLS_MANIFEST (if it's a path to JSON)
-      3) fallback: app/manifests/tools_manifest.json
+    ChatGPT Actions are REST-style request/response calls (no WebSocket client) and
+    typically operate on JSON bodies. This endpoint filters the relay's full OpenAPI
+    schema down to an allowlist of Action-friendly paths (see MANIFEST["meta"]).
     """
-    settings = get_settings()
-    manifest_setting: Union[str, List[Dict[str, Any]], None] = getattr(settings, "TOOLS_MANIFEST", None)
-
-    # If someone injected the tools directly (already parsed)
-    if isinstance(manifest_setting, list):
-        return manifest_setting
-
-    # If it's a path string
-    if isinstance(manifest_setting, str) and manifest_setting.strip():
-        path = Path(manifest_setting)
-        if path.exists():
-            try:
-                return _extract_tools(_read_json(path))
-            except Exception as e:
-                logger.warning("Failed reading TOOLS_MANIFEST from %s: %s", path, e)
-
-    # Fallback to app/manifests/tools_manifest.json relative to this file
-    fallback_path = Path(__file__).resolve().parents[1] / "manifests" / "tools_manifest.json"
-    if fallback_path.exists():
-        try:
-            return _extract_tools(_read_json(fallback_path))
-        except Exception as e:
-            logger.warning("Failed reading fallback tools manifest from %s: %s", fallback_path, e)
-
-    return []
-
-
-def build_manifest_response(tools: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
-    settings = get_settings()
-    tools_list = tools if tools is not None else load_tools_manifest()
-
-    # Keep current behavior for tests and clients.
-    endpoints: Dict[str, List[str]] = {
-        # Option A: single Action-friendly proxy entrypoint.
-        "proxy": ["/v1/proxy"],
-        "responses": ["/v1/responses", "/v1/responses/compact"],
-        "responses_compact": ["/v1/responses/compact"],
-    }
+    full = request.app.openapi()
 
-    relay_name = (
-        getattr(settings, "relay_name", None)
-        or getattr(settings, "project_name", None)
-        or "ChatGPT Team Relay"
-    )
-
-    # IMPORTANT: We intentionally do not list multipart/binary families (e.g., /v1/uploads)
-    # in this tools manifest. Those routes may exist in the app (see /openapi.json) but are
-    # excluded from the Actions-safe tool surface by design.
-    meta: Dict[str, Any] = {
-        "generated_at": datetime.now(timezone.utc).isoformat(),
-        "relay_name": relay_name,
-        "manifest_scope": "actions_safe",
-        "option": "A",
-        "openapi_url": "/openapi.json",
-        "endpoints_note": (
-            "This manifest is a curated, JSON-only tool surface. "
-            "Multipart/binary route families (e.g., Uploads) are intentionally excluded; "
-            "refer to /openapi.json for the full route inventory."
-        ),
-    }
-
-    return {
-        "object": "list",
-        "data": tools_list,
-        "endpoints": endpoints,
-        "meta": meta,
-    }
+    groups = MANIFEST.get("meta", {}).get("actions_openapi_groups") or []
+    allowed_paths: set[str] = set()
+    for g in groups:
+        allowed_paths.update(MANIFEST.get("endpoints", {}).get(str(g), []))
 
+    allowed_paths.update({"/health", "/v1/health"})
 
-@router.get("/manifest")
-async def get_manifest_root() -> Dict[str, Any]:
-    logger.info("Serving tools manifest (root alias)")
-    return build_manifest_response()
+    filtered = copy.deepcopy(full)
+    filtered["paths"] = {
+        path: spec
+        for path, spec in (full.get("paths") or {}).items()
+        if path in allowed_paths
+    }
 
+    info = filtered.get("info") or {}
+    title = str(info.get("title") or "OpenAPI")
+    info["title"] = f"{title} (Actions subset)"
+    filtered["info"] = info
 
-@router.get("/v1/manifest")
-async def get_manifest_v1() -> Dict[str, Any]:
-    logger.info("Serving tools manifest (/v1)")
-    return build_manifest_response()
+    return JSONResponse(filtered)
diff --git a/app/routes/images.py b/app/routes/images.py
index 0da60ac..11a40e2 100755
--- a/app/routes/images.py
+++ b/app/routes/images.py
@@ -1,11 +1,183 @@
-from fastapi import APIRouter, Request
+from __future__ import annotations
+
+import base64
+import binascii
+import ipaddress
+from typing import Dict, Optional, Tuple
+from urllib.parse import urlparse
+
+import httpx
+from fastapi import APIRouter, HTTPException, Request
+from pydantic import BaseModel, Field
 from starlette.responses import Response
 
-from app.api.forward_openai import forward_openai_request
+from app.api.forward_openai import build_upstream_url, forward_openai_request
+from app.core.config import settings
+from app.core.http_client import get_async_httpx_client
 from app.utils.logger import relay_log as logger
 
 router = APIRouter(prefix="/v1", tags=["images"])
 
+# Hard safety limit for server-side URL/base64 ingestion (Actions wrapper endpoints).
+# This is NOT an OpenAI limit; it's a relay safety limit to avoid large downloads/memory spikes.
+_MAX_ACTION_INPUT_BYTES = 10 * 1024 * 1024  # 10 MiB
+
+
+def _bad_request(detail: str) -> None:
+    raise HTTPException(status_code=400, detail=detail)
+
+
+def _validate_fetch_url(url: str) -> None:
+    """
+    Minimal SSRF guard for Actions wrapper endpoints.
+
+    Assumptions:
+      - Actions provide HTTPS file URLs (common for ChatGPT file URL model).
+      - We explicitly refuse localhost / private IP literals.
+      - We do not perform DNS resolution here (to keep this lightweight).
+    """
+    parsed = urlparse(url)
+    if parsed.scheme not in ("https",):
+        _bad_request("Only https:// URLs are allowed for Actions image wrappers.")
+
+    host = (parsed.hostname or "").strip()
+    if not host:
+        _bad_request("Invalid URL.")
+
+    host_l = host.lower()
+    if host_l in {"localhost"} or host_l.endswith(".local"):
+        _bad_request("Refusing to fetch from local hostnames.")
+
+    # If hostname is a literal IP address, block private/reserved ranges.
+    try:
+        ip = ipaddress.ip_address(host_l)
+        if (
+            ip.is_private
+            or ip.is_loopback
+            or ip.is_link_local
+            or ip.is_reserved
+            or ip.is_multicast
+            or ip.is_unspecified
+        ):
+            _bad_request("Refusing to fetch from private or local network addresses.")
+    except ValueError:
+        # Not a literal IP; could still resolve to one, but we avoid DNS resolution here.
+        pass
+
+
+async def _fetch_bytes(url: str) -> Tuple[bytes, str]:
+    _validate_fetch_url(url)
+    client = get_async_httpx_client()
+
+    try:
+        r = await client.get(url, follow_redirects=True)
+    except httpx.HTTPError as e:
+        raise HTTPException(status_code=502, detail=f"Failed to fetch URL: {e}") from e
+
+    if r.status_code >= 400:
+        raise HTTPException(status_code=502, detail=f"Failed to fetch URL (HTTP {r.status_code}).")
+
+    blob = r.content
+    if len(blob) > _MAX_ACTION_INPUT_BYTES:
+        _bad_request(f"Fetched object too large ({len(blob)} bytes).")
+
+    content_type = (r.headers.get("content-type") or "application/octet-stream").split(";", 1)[0].strip()
+    return blob, content_type
+
+
+def _decode_base64(data_b64: str) -> bytes:
+    # Accept both raw base64 and data: URLs.
+    if data_b64.startswith("data:"):
+        try:
+            _, b64_part = data_b64.split(",", 1)
+        except ValueError:
+            _bad_request("Invalid data: URL for base64 payload.")
+        data_b64 = b64_part
+
+    try:
+        blob = base64.b64decode(data_b64, validate=True)
+    except (binascii.Error, ValueError) as e:
+        _bad_request(f"Invalid base64 payload: {e}")
+
+    if len(blob) > _MAX_ACTION_INPUT_BYTES:
+        _bad_request(f"Decoded object too large ({len(blob)} bytes).")
+
+    return blob
+
+
+async def _resolve_blob(*, url: Optional[str], b64: Optional[str], label: str) -> Tuple[bytes, str]:
+    """
+    Resolve a binary blob either from a URL fetch or a base64 payload.
+    Returns: (bytes, content_type)
+    """
+    if bool(url) == bool(b64):
+        _bad_request(f"Provide exactly one of {label}_url or {label}_base64.")
+
+    if url:
+        blob, content_type = await _fetch_bytes(url)
+        return blob, content_type
+
+    assert b64 is not None
+    # Default to PNG when the client didn't send an explicit MIME type.
+    return _decode_base64(b64), "image/png"
+
+
+def _coerce_multipart_data(d: Dict[str, object]) -> Dict[str, str]:
+    """httpx multipart 'data=' fields must be string-ish."""
+    out: Dict[str, str] = {}
+    for k, v in d.items():
+        if v is None:
+            continue
+        out[k] = str(v)
+    return out
+
+
+def _pydantic_dump(model: BaseModel) -> Dict[str, object]:
+    # Pydantic v2 uses model_dump; v1 uses dict.
+    if hasattr(model, "model_dump"):
+        return model.model_dump(exclude_none=True)  # type: ignore[no-any-return]
+    return model.dict(exclude_none=True)  # type: ignore[no-any-return]
+
+
+def _upstream_headers(request: Request) -> Dict[str, str]:
+    """
+    Build upstream headers for server-to-server wrapper calls.
+    We intentionally do NOT forward relay auth headers (X-Relay-Key).
+    """
+    headers: Dict[str, str] = {
+        "Authorization": f"Bearer {settings.openai_api_key}",
+        "Accept": "application/json",
+    }
+
+    # Optional org/project overrides if your clients set them.
+    for h in ("OpenAI-Organization", "OpenAI-Project", "OpenAI-Beta"):
+        v = request.headers.get(h)
+        if v:
+            headers[h] = v
+
+    return headers
+
+
+def _response_from_upstream(r: httpx.Response) -> Response:
+    media_type = (r.headers.get("content-type") or "application/octet-stream").split(";", 1)[0].strip()
+
+    passthrough_headers: Dict[str, str] = {}
+    for h in ("x-request-id", "openai-request-id"):
+        v = r.headers.get(h)
+        if v:
+            passthrough_headers[h] = v
+
+    return Response(
+        content=r.content,
+        status_code=r.status_code,
+        headers=passthrough_headers,
+        media_type=media_type,
+    )
+
+
+# ---------------------------------------------------------------------------
+# Standard OpenAI-compatible image routes (pass-through)
+# ---------------------------------------------------------------------------
 
 @router.post("/images", summary="Create image generation")
 @router.post("/images/generations", summary="Create image generation (alias)")
@@ -24,3 +196,120 @@ async def edit_image(request: Request) -> Response:
 async def variations_image(request: Request) -> Response:
     logger.info("→ [images] %s %s (variations)", request.method, request.url.path)
     return await forward_openai_request(request)
+
+
+# ---------------------------------------------------------------------------
+# Actions-friendly wrappers (JSON in, relay builds multipart upstream)
+# ---------------------------------------------------------------------------
+
+class ActionImageEditRequest(BaseModel):
+    # Standard OpenAI fields
+    prompt: str = Field(..., description="Text prompt describing the desired edit.")
+    model: Optional[str] = Field(default=None, description="Image model (e.g., gpt-image-1, dall-e-2).")
+    n: Optional[int] = Field(default=None, ge=1, le=10)
+    size: Optional[str] = None
+    response_format: Optional[str] = None
+    user: Optional[str] = None
+
+    # Actions-friendly image inputs
+    image_url: Optional[str] = Field(default=None, description="HTTPS URL to the base image.")
+    image_base64: Optional[str] = Field(default=None, description="Base64 (or data: URL) for the base image.")
+    mask_url: Optional[str] = Field(default=None, description="HTTPS URL to the mask image (optional).")
+    mask_base64: Optional[str] = Field(default=None, description="Base64 (or data: URL) for the mask (optional).")
+
+    # Optional filenames (cosmetic)
+    image_filename: str = "image.png"
+    mask_filename: str = "mask.png"
+
+
+class ActionImageVariationRequest(BaseModel):
+    model: Optional[str] = None
+    n: Optional[int] = Field(default=None, ge=1, le=10)
+    size: Optional[str] = None
+    response_format: Optional[str] = None
+    user: Optional[str] = None
+
+    image_url: Optional[str] = None
+    image_base64: Optional[str] = None
+    image_filename: str = "image.png"
+
+
+@router.post(
+    "/actions/images/edits",
+    summary="Actions-friendly image edit (JSON url/base64 → multipart upstream)",
+)
+async def actions_image_edits(payload: ActionImageEditRequest, request: Request) -> Response:
+    logger.info("→ [actions/images] %s %s", request.method, request.url.path)
+
+    image_bytes, image_ct = await _resolve_blob(url=payload.image_url, b64=payload.image_base64, label="image")
+    if not image_ct.startswith("image/"):
+        _bad_request(f"image must be an image/* content-type (got {image_ct}).")
+
+    mask_bytes: Optional[bytes] = None
+    mask_ct: Optional[str] = None
+    if payload.mask_url or payload.mask_base64:
+        mask_bytes, mask_ct = await _resolve_blob(url=payload.mask_url, b64=payload.mask_base64, label="mask")
+        if not mask_ct.startswith("image/"):
+            _bad_request(f"mask must be an image/* content-type (got {mask_ct}).")
+
+    data_obj = _pydantic_dump(payload)
+
+    # Remove wrapper-only fields before sending upstream.
+    for k in (
+        "image_url",
+        "image_base64",
+        "mask_url",
+        "mask_base64",
+        "image_filename",
+        "mask_filename",
+    ):
+        data_obj.pop(k, None)
+
+    files: Dict[str, tuple[str, bytes, str]] = {
+        "image": (payload.image_filename, image_bytes, image_ct),
+    }
+    if mask_bytes is not None and mask_ct is not None:
+        files["mask"] = (payload.mask_filename, mask_bytes, mask_ct)
+
+    upstream_url = build_upstream_url("/v1/images/edits")
+    client = get_async_httpx_client()
+
+    r = await client.post(
+        upstream_url,
+        headers=_upstream_headers(request),
+        data=_coerce_multipart_data(data_obj),
+        files=files,
+    )
+    return _response_from_upstream(r)
+
+
+@router.post(
+    "/actions/images/variations",
+    summary="Actions-friendly image variations (JSON url/base64 → multipart upstream)",
+)
+async def actions_image_variations(payload: ActionImageVariationRequest, request: Request) -> Response:
+    logger.info("→ [actions/images] %s %s", request.method, request.url.path)
+
+    image_bytes, image_ct = await _resolve_blob(url=payload.image_url, b64=payload.image_base64, label="image")
+    if not image_ct.startswith("image/"):
+        _bad_request(f"image must be an image/* content-type (got {image_ct}).")
+
+    data_obj = _pydantic_dump(payload)
+
+    for k in ("image_url", "image_base64", "image_filename"):
+        data_obj.pop(k, None)
+
+    files: Dict[str, tuple[str, bytes, str]] = {
+        "image": (payload.image_filename, image_bytes, image_ct),
+    }
+
+    upstream_url = build_upstream_url("/v1/images/variations")
+    client = get_async_httpx_client()
+
+    r = await client.post(
+        upstream_url,
+        headers=_upstream_headers(request),
+        data=_coerce_multipart_data(data_obj),
+        files=files,
+    )
+    return _response_from_upstream(r)
diff --git a/project-tree.md b/project-tree.md
index 59f821d..851e1e0 100755
--- a/project-tree.md
+++ b/project-tree.md
@@ -12,6 +12,8 @@
   📄 chatgpt_changes.md
   📄 chatgpt_sync.sh
   📄 generate_tree.py
+  📄 input.png
+  📄 input_256.png
   📄 openai_models_2025-11.csv
   📄 project-tree.md
   📄 pytest.ini
@@ -98,6 +100,9 @@
       📄 videos.db
   📁 docs
     📄 README.md
+  📁 path
+    📁 to
+      📄 input.png
   📁 schemas
     📄 __init__.py
     📄 openapi.yaml
@@ -121,6 +126,7 @@
     📄 conftest.py
     📄 test_extended_routes_smoke_integration.py
     📄 test_files_and_batches_integration.py
+    📄 test_images_variations_integration.py
     📄 test_local_e2e.py
     📄 test_relay_auth_guard.py
     📄 test_remaining_routes_smoke_integration.py
diff --git a/tests/test_images_variations_integration - Copy.py b/tests/test_images_variations_integration - Copy.py
deleted file mode 100644
index cd2022d..0000000
--- a/tests/test_images_variations_integration - Copy.py	
+++ /dev/null
@@ -1,80 +0,0 @@
-import binascii
-import os
-import struct
-import zlib
-from typing import Dict
-
-import pytest
-import requests
-
-RELAY_BASE_URL = os.getenv("RELAY_BASE_URL", "http://localhost:8000").rstrip("/")
-RELAY_TOKEN = os.getenv("RELAY_TOKEN", "")
-DEFAULT_TIMEOUT_S = 20
-
-
-def _auth_headers() -> Dict[str, str]:
-    if not RELAY_TOKEN:
-        pytest.skip("RELAY_TOKEN not set")
-    return {"Authorization": f"Bearer {RELAY_TOKEN}"}
-
-
-def _skip_if_no_real_key() -> None:
-    # Integration tests tolerate 4xx from upstream but should not run
-    # without a real OpenAI key behind the relay.
-    if not os.getenv("INTEGRATION_OPENAI_API_KEY"):
-        pytest.skip("INTEGRATION_OPENAI_API_KEY not set")
-
-
-def _make_rgba_png_bytes(width: int, height: int, rgba=(0, 0, 0, 0)) -> bytes:
-    """
-    Create a minimal, valid RGBA PNG using only the standard library.
-    Avoids committing binary fixtures and avoids pillow dependency.
-    """
-    r, g, b, a = rgba
-
-    # Each row: filter byte (0) + width * RGBA bytes
-    row = bytes([0]) + bytes([r, g, b, a]) * width
-    raw = row * height
-    compressed = zlib.compress(raw)
-
-    def _chunk(chunk_type: bytes, data: bytes) -> bytes:
-        crc = binascii.crc32(chunk_type + data) & 0xFFFFFFFF
-        return struct.pack("!I", len(data)) + chunk_type + data + struct.pack("!I", crc)
-
-    # IHDR: width, height, bit depth=8, color type=6 (RGBA), compression=0, filter=0, interlace=0
-    ihdr = struct.pack("!IIBBBBB", width, height, 8, 6, 0, 0, 0)
-
-    return (
-        b"\x89PNG\r\n\x1a\n"
-        + _chunk(b"IHDR", ihdr)
-        + _chunk(b"IDAT", compressed)
-        + _chunk(b"IEND", b"")
-    )
-
-
-def test_openapi_has_images_variations_path() -> None:
-    r = requests.get(f"{RELAY_BASE_URL}/openapi.json", timeout=DEFAULT_TIMEOUT_S)
-    assert r.status_code == 200
-    paths = r.json().get("paths", {})
-    assert "/v1/images/variations" in paths, "missing /v1/images/variations in OpenAPI schema"
-
-
-def test_images_variations_wiring_no_5xx(tmp_path) -> None:
-    _skip_if_no_real_key()
-
-    img_path = tmp_path / "input.png"
-    img_path.write_bytes(_make_rgba_png_bytes(256, 256))
-
-    # Use an intentionally invalid model to avoid billable generations while still
-    # exercising multipart wiring end-to-end.
-    data = {"model": "__invalid_model__", "n": "1", "size": "256x256"}
-    files = {"image": ("input.png", img_path.read_bytes(), "image/png")}
-
-    r = requests.post(
-        f"{RELAY_BASE_URL}/v1/images/variations",
-        headers=_auth_headers(),
-        data=data,
-        files=files,
-        timeout=DEFAULT_TIMEOUT_S,
-    )
-    assert r.status_code < 500, r.text
```

## CURRENT CONTENT OF CHANGED FILES (WORKTREE)

## FILE: tests/test_images_variations_integration - Copy.py @ WORKTREE
> Deleted in worktree.

## FILE: app/api/tools_api.py @ WORKTREE
```
from __future__ import annotations

import copy
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.core.config import settings

# This router serves:
#   - /manifest: a lightweight capability manifest for human/dev tooling
#   - /openapi.actions.json: a curated OpenAPI subset suitable for ChatGPT Actions

router = APIRouter()

MANIFEST: dict[str, Any] = {
    "object": "relay.manifest",
    "data": [],
    "endpoints": {
        "health": ["/health", "/v1/health"],
        "models": ["/v1/models", "/v1/models/{model}"],
        "responses": ["/v1/responses", "/v1/responses/compact"],
        "embeddings": ["/v1/embeddings"],
        "images": ["/v1/images/generations"],
        "images_actions": ["/v1/actions/images/variations", "/v1/actions/images/edits"],
        "files": ["/v1/files", "/v1/files/{file_id}", "/v1/files/{file_id}/content"],
        "uploads": [
            "/v1/uploads",
            "/v1/uploads/{upload_id}",
            "/v1/uploads/{upload_id}/parts",
            "/v1/uploads/{upload_id}/complete",
            "/v1/uploads/{upload_id}/cancel",
        ],
        "batches": ["/v1/batches", "/v1/batches/{batch_id}"],
        "proxy": ["/v1/proxy"],
    },
    "meta": {
        "relay_name": "chatgpt-team relay",
        "auth_required": settings.RELAY_AUTH_ENABLED,
        "auth_header": "X-Relay-Key",
        "upstream_base_url": settings.UPSTREAM_BASE_URL,
        "actions_openapi_url": "/openapi.actions.json",
        "actions_openapi_groups": [
            "health",
            "models",
            "responses",
            "embeddings",
            "images",
            "images_actions",
            "proxy",
        ],
    },
}


@router.get("/manifest", include_in_schema=False)
@router.get("/v1/manifest", include_in_schema=False)
async def get_manifest() -> dict[str, Any]:
    return MANIFEST


@router.get("/openapi.actions.json", include_in_schema=False)
async def openapi_actions(request: Request) -> JSONResponse:
    """
    Return an Actions-safe OpenAPI schema.

    ChatGPT Actions are REST-style request/response calls (no WebSocket client) and
    typically operate on JSON bodies. This endpoint filters the relay's full OpenAPI
    schema down to an allowlist of Action-friendly paths (see MANIFEST["meta"]).
    """
    full = request.app.openapi()

    groups = MANIFEST.get("meta", {}).get("actions_openapi_groups") or []
    allowed_paths: set[str] = set()
    for g in groups:
        allowed_paths.update(MANIFEST.get("endpoints", {}).get(str(g), []))

    allowed_paths.update({"/health", "/v1/health"})

    filtered = copy.deepcopy(full)
    filtered["paths"] = {
        path: spec
        for path, spec in (full.get("paths") or {}).items()
        if path in allowed_paths
    }

    info = filtered.get("info") or {}
    title = str(info.get("title") or "OpenAPI")
    info["title"] = f"{title} (Actions subset)"
    filtered["info"] = info

    return JSONResponse(filtered)
```

## FILE: app/routes/images.py @ WORKTREE
```
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
```

## FILE: project-tree.md @ WORKTREE
```
  📄 .env.env
  📄 .env.example.env
  📄 .gitattributes
  📄 .gitignore
  📄 .gitleaks.toml
  📄 AGENTS.md
  📄 ChatGPT-API_reference_ground_truth-2025-10-29.pdf
  📄 RELAY_CHECKLIST_v16.md
  📄 RELAY_PROGRESS_SUMMARY_v12.md
  📄 __init__.py
  📄 chatgpt_baseline.md
  📄 chatgpt_changes.md
  📄 chatgpt_sync.sh
  📄 generate_tree.py
  📄 input.png
  📄 input_256.png
  📄 openai_models_2025-11.csv
  📄 project-tree.md
  📄 pytest.ini
  📄 render.yaml
  📄 requirements.txt
  📁 app
    📄 __init__.py
    📄 http_client.py
    📄 main.py
    📁 api
      📄 __init__.py
      📄 forward_openai.py
      📄 routes.py
      📄 sse.py
      📄 tools_api.py
    📁 core
      📄 __init__.py
      📄 config.py
      📄 http_client.py
      📄 logging.py
    📁 manifests
      📄 __init__.py
      📄 tools_manifest.json
    📁 middleware
      📄 __init__.py
      📄 p4_orchestrator.py
      📄 relay_auth.py
      📄 validation.py
    📁 models
      📄 __init__.py
      📄 error.py
    📁 routes
      📄 __init__.py
      📄 actions.py
      📄 batches.py
      📄 containers.py
      📄 conversations.py
      📄 embeddings.py
      📄 files.py
      📄 health.py
      📄 images.py
      📄 models.py
      📄 proxy.py
      📄 realtime.py
      📄 register_routes.py
      📄 responses.py
      📄 uploads.py
      📄 vector_stores.py
      📄 videos.py
    📁 utils
      📄 __init__.py
      📄 authy.py
      📄 error_handler.py
      📄 http_client.py
      📄 logger.py
  📁 chatgpt_team_relay.egg-info
    📄 PKG-INFO
    📄 SOURCES.txt
    📄 dependency_links.txt
    📄 requires.txt
    📄 top_level.txt
  📁 data
    📁 conversations
    📁 embeddings
      📄 embeddings.db
    📁 files
      📄 files.db
    📁 images
      📄 images.db
    📁 jobs
      📄 jobs.db
    📁 models
      📄 models.db
      📄 openai_models_categorized.csv
      📄 openai_models_categorized.json
    📁 uploads
      📄 attachments.db
      📄 file_9aa498e1dbb0
    📁 usage
      📄 usage.db
    📁 vector_stores
      📄 vectors.db
    📁 videos
      📄 videos.db
  📁 docs
    📄 README.md
  📁 path
    📁 to
      📄 input.png
  📁 schemas
    📄 __init__.py
    📄 openapi.yaml
  📁 scripts
    📄 batch_download_test.sh
    📄 content_endpoints_smoke.sh
    📄 openapi_operationid_check.sh
    📄 run_success_gates.sh
    📄 sse_smoke_test.sh
    📄 test_local.sh
    📄 test_render.sh
    📄 test_success_gates_integration.sh
    📄 uploads_e2e_test.sh
  📁 static
    📁 .well-known
      📄 __init__.py
      📄 ai-plugin.json
  📁 tests
    📄 __init__.py
    📄 client.py
    📄 conftest.py
    📄 test_extended_routes_smoke_integration.py
    📄 test_files_and_batches_integration.py
    📄 test_images_variations_integration.py
    📄 test_local_e2e.py
    📄 test_relay_auth_guard.py
    📄 test_remaining_routes_smoke_integration.py
    📄 test_success_gates_integration.py```

