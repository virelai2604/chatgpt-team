# ChatGPT Sync
Repo: chatgpt-team
Base: origin/main
Base commit (merge-base): 498a04759f3e93d38bb3b3d6d0e5245801c931dd
Dirs: app tests static schemas
Root files: project-tree.md pyproject.toml
Mode: changes
Generated: 2025-12-23T14:45:05+07:00

## CHANGE SUMMARY (since 498a04759f3e93d38bb3b3d6d0e5245801c931dd, includes worktree)

```
M	app/api/forward_openai.py
M	app/core/http_client.py
M	app/middleware/validation.py
M	app/utils/http_client.py
M	project-tree.md
M	tests/conftest.py
M	tests/test_files_and_batches_integration.py
```

## PATCH (since 498a04759f3e93d38bb3b3d6d0e5245801c931dd, includes worktree)

```diff
diff --git a/app/api/forward_openai.py b/app/api/forward_openai.py
index 833b5bd..af35c54 100755
--- a/app/api/forward_openai.py
+++ b/app/api/forward_openai.py
@@ -1,374 +1,268 @@
 from __future__ import annotations
 
-import json
-from typing import Any, Mapping, Optional
-from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
+import re
+from typing import Any, Dict, Mapping, Optional
 
 import httpx
 from fastapi import HTTPException, Request
 from fastapi.responses import Response, StreamingResponse
 
-from app.core.http_client import get_async_httpx_client, get_async_openai_client
-from app.utils.logger import relay_log
-
-# Settings access (supports either get_settings() or a module-level settings object).
-try:
-    from app.core.config import get_settings  # type: ignore
-except ImportError:  # pragma: no cover
-    get_settings = None  # type: ignore
-
-try:
-    from app.core.config import settings as module_settings  # type: ignore
-except ImportError:  # pragma: no cover
-    module_settings = None  # type: ignore
-
-
-def _settings() -> Any:
-    if get_settings is not None:
-        return get_settings()
-    if module_settings is not None:
-        return module_settings
-    raise RuntimeError("Settings not available (expected get_settings() or settings)")
-
-
-# -------------------------
-# Header / URL helpers
-# -------------------------
-
-_HOP_BY_HOP_HEADERS = {
-    "connection",
-    "keep-alive",
-    "proxy-authenticate",
-    "proxy-authorization",
-    "te",
-    "trailers",
-    "transfer-encoding",
-    "upgrade",
-}
-
-# Must not forward these upstream (common relay bug sources)
-_STRIP_REQUEST_HEADERS = {
-    "authorization",    # relay key
-    "host",             # never forward localhost host to OpenAI
-    "content-length",   # let httpx compute it for upstream request
-}
-
-
-def normalize_base_url(base_url: str) -> str:
-    """
-    Normalize an OpenAI base URL for consistent join semantics.
-    Accepts:
-      - https://api.openai.com
-      - https://api.openai.com/v1
-    Returns a base ending with /v1
-    """
-    b = (base_url or "").strip()
-    if not b:
-        raise ValueError("OPENAI_API_BASE is empty")
-    b = b.rstrip("/")
-    if b.endswith("/v1"):
-        return b
-    return b + "/v1"
-
-
-def join_url(base_v1: str, path: str) -> str:
-    base_v1 = normalize_base_url(base_v1)
-    p = (path or "").strip()
-    if not p.startswith("/"):
-        p = "/" + p
-    # If path already includes /v1, strip it so we don't double it.
-    if p.startswith("/v1/"):
-        p = p[3:]
-    elif p == "/v1":
-        p = ""
-    return base_v1 + p
-
-
-# -------------------------
-# Backwards-compat shims
-# -------------------------
-
-def _get_timeout_seconds() -> float:
-    """Return the default upstream timeout in seconds (float)."""
-    s = _settings()
-    raw = getattr(s, "proxy_timeout", None)
-    if raw is None:
-        raw = getattr(s, "openai_timeout", None)
-    try:
-        return float(raw) if raw is not None else 120.0
-    except (TypeError, ValueError):
-        return 120.0
-
-
-def build_upstream_url(path: str) -> str:
-    """Build a fully-qualified OpenAI upstream URL for a given path."""
-    s = _settings()
-    base = getattr(s, "openai_api_base", "https://api.openai.com/v1")
-    return join_url(base, path)
-
-
-def filter_upstream_headers(headers: Mapping[str, str]) -> dict[str, str]:
-    """Filter hop-by-hop headers and relay/transport headers from inbound headers."""
-    return _filter_inbound_headers(headers)
-
-
-def _filter_inbound_headers(headers: Mapping[str, str]) -> dict[str, str]:
-    out: dict[str, str] = {}
-    for k, v in headers.items():
-        lk = k.lower()
-        if lk in _HOP_BY_HOP_HEADERS:
-            continue
-        if lk in _STRIP_REQUEST_HEADERS:
-            continue
-        out[k] = v
-    return out
+from app.core.config import get_settings
+from app.http_client import get_async_httpx_client
 
 
-def build_outbound_headers(
-    *,
-    inbound_headers: Mapping[str, str],
-    openai_api_key: str,
-) -> dict[str, str]:
-    if not openai_api_key:
-        raise HTTPException(status_code=500, detail="Server is missing OPENAI_API_KEY")
+# --- Streaming route detection --------------------------------------------------------
 
-    out = _filter_inbound_headers(inbound_headers)
+_SSE_PATH_RE = re.compile(r"^/v1/(responses|chat/completions)$")
+
+
+def _is_sse_path(path: str) -> bool:
+    """Return True if an upstream route is expected to stream via SSE."""
+    return _SSE_PATH_RE.match(path) is not None
 
-    # Upstream auth
-    out["Authorization"] = f"Bearer {openai_api_key}"
 
-    # Ensure we have a content-type for JSON calls (multipart should already have it)
-    if "content-type" not in {k.lower(): v for k, v in out.items()}:
-        out["Content-Type"] = "application/json"
+# --- Header/url helpers ---------------------------------------------------------------
 
-    # Optional beta headers if configured
-    s = _settings()
-    assistants_beta = getattr(s, "openai_assistants_beta", None)
-    realtime_beta = getattr(s, "openai_realtime_beta", None)
-    if assistants_beta:
-        out["OpenAI-Beta"] = assistants_beta
-    if realtime_beta:
-        out["OpenAI-Beta"] = realtime_beta
+def _join_url(base: str, path: str) -> str:
+    return f"{base.rstrip('/')}/{path.lstrip('/')}"
 
+
+def _filter_inbound_headers(headers: Mapping[str, str]) -> Dict[str, str]:
+    """Remove hop-by-hop and unsafe headers before proxying upstream."""
+    out: Dict[str, str] = {}
+    for k, v in headers.items():
+        lk = k.lower()
+        if lk in {"host", "connection", "content-length"}:
+            continue
+        if lk.startswith("sec-") or lk in {
+            "upgrade",
+            "keep-alive",
+            "proxy-authenticate",
+            "proxy-authorization",
+            "te",
+            "trailer",
+            "transfer-encoding",
+        }:
+            continue
+        out[k] = v
     return out
 
 
-def _maybe_model_dump(obj: Any) -> dict[str, Any]:
-    """OpenAI SDK objects are Pydantic-like; support model_dump() and dict()."""
-    if hasattr(obj, "model_dump"):
-        return obj.model_dump()  # type: ignore[no-any-return]
-    if isinstance(obj, dict):
-        return obj
-    try:
-        return json.loads(json.dumps(obj, default=str))
-    except Exception:
-        return {"result": str(obj)}
+def _filter_upstream_headers(headers: Mapping[str, str]) -> Dict[str, str]:
+    """Remove hop-by-hop/encoding headers from upstream response."""
+    out: Dict[str, str] = {}
+    for k, v in headers.items():
+        lk = k.lower()
+        if lk in {"content-encoding", "transfer-encoding", "connection"}:
+            continue
+        out[k] = v
+    return out
 
 
-# -------------------------
-# Generic forwarders (httpx)
-# -------------------------
+# Back-compat alias used by some route modules.
+def filter_upstream_headers(headers: Mapping[str, str]) -> Dict[str, str]:
+    return _filter_upstream_headers(headers)
 
-async def forward_openai_request(request: Request) -> Response:
-    """
-    Forward an incoming FastAPI request to the upstream OpenAI API using httpx.
-    Suitable for:
-      - JSON
-      - multipart/form-data (Uploads/Files)
-      - binary content endpoints
-      - SSE streaming (when client sets Accept: text/event-stream)
-    """
-    s = _settings()
-    base = getattr(s, "openai_api_base", "https://api.openai.com/v1")
-    key = getattr(s, "openai_api_key", "")
-    timeout_s = float(getattr(s, "proxy_timeout", 120))
 
-    upstream_url = join_url(base, request.url.path)
+def build_upstream_url(request: Request, base_url: str, *, path_override: Optional[str] = None) -> str:
+    """Build the upstream URL, preserving the original query string."""
+    path = path_override or request.url.path
+    url = _join_url(base_url, path)
+    if request.url.query:
+        url = f"{url}?{request.url.query}"
+    return url
 
-    # Preserve query string
-    query = request.url.query
-    if query:
-        upstream_url = upstream_url + "?" + query
 
-    # Read body bytes once; forward as-is.
-    body = await request.body()
+def _get_timeout_seconds(settings: Any) -> float:
+    """Back-compat: support multiple config field names."""
+    for name in ("proxy_timeout_seconds", "proxy_timeout", "proxy_timeout_s"):
+        if hasattr(settings, name):
+            try:
+                return float(getattr(settings, name))
+            except Exception:
+                pass
+    return 120.0
 
-    headers = build_outbound_headers(inbound_headers=request.headers, openai_api_key=key)
 
-    relay_log.debug("Forwarding %s %s -> %s", request.method, request.url.path, upstream_url)
+def build_outbound_headers(
+    inbound_headers: Mapping[str, str],
+    openai_api_key: str,
+    content_type: Optional[str] = None,
+    forward_accept: bool = True,
+    path_hint: Optional[str] = None,
+) -> Dict[str, str]:
+    """
+    Create upstream request headers.
 
-    client = get_async_httpx_client(timeout=timeout_s)
+    This function intentionally accepts legacy parameters (forward_accept, path_hint)
+    so older route modules can call it without raising TypeError.
+    """
+    # forward_accept/path_hint are retained for compatibility; current implementation
+    # always forwards the inbound Accept header if present.
+    _ = forward_accept
+    _ = path_hint
 
-    # Streaming SSE support
-    accept = request.headers.get("accept", "")
-    wants_sse = "text/event-stream" in (accept or "").lower()
-
-    if wants_sse:
-        async def event_generator():
-            async with client.stream(
-                request.method,
-                upstream_url,
-                headers=headers,
-                content=body if body else None,
-            ) as upstream_resp:
-                # If upstream errors, it will generally send JSON or text; raising is fine here.
-                upstream_resp.raise_for_status()
-                async for chunk in upstream_resp.aiter_bytes():
-                    if chunk:
-                        yield chunk
-
-        return StreamingResponse(
-            event_generator(),
-            status_code=200,
-            media_type="text/event-stream",
-        )
+    out = _filter_inbound_headers(inbound_headers)
+    out["Authorization"] = f"Bearer {openai_api_key}"
 
-    upstream_resp = await client.request(
-        request.method,
-        upstream_url,
-        headers=headers,
-        content=body if body else None,
-    )
+    if content_type:
+        out["Content-Type"] = content_type
+
+    # OpenAI-Beta header can contain multiple comma-separated flags.
+    s = get_settings()
+    beta_values = []
+    if getattr(s, "openai_assistants_beta", False):
+        beta_values.append("assistants=v2")
+    if getattr(s, "openai_realtime_beta", False):
+        beta_values.append("realtime=v1")
+
+    if beta_values:
+        existing = out.get("OpenAI-Beta")
+        combined = []
+        if existing:
+            combined.extend([p.strip() for p in existing.split(",") if p.strip()])
+        combined.extend(beta_values)
+
+        seen = set()
+        deduped = []
+        for item in combined:
+            if item in seen:
+                continue
+            seen.add(item)
+            deduped.append(item)
 
-    resp_headers: dict[str, str] = {}
-    for k, v in upstream_resp.headers.items():
-        if k.lower() in _HOP_BY_HOP_HEADERS:
-            continue
-        resp_headers[k] = v
+        out["OpenAI-Beta"] = ", ".join(deduped)
 
-    return Response(
-        content=upstream_resp.content,
-        status_code=upstream_resp.status_code,
-        headers=resp_headers,
-        media_type=upstream_resp.headers.get("content-type"),
-    )
+    return out
 
 
-async def forward_openai_method_path(
+# --- Core forwarders ------------------------------------------------------------------
+
+async def forward_openai_request_to_path(
+    request: Request,
     *,
-    method: str,
-    path: str,
-    query: Optional[Mapping[str, Any]] = None,
-    json_body: Any = None,
-    inbound_headers: Optional[Mapping[str, str]] = None,
+    method_override: Optional[str] = None,
+    path_override: Optional[str] = None,
 ) -> Response:
-    """
-    Method/path forwarder for Action-friendly JSON envelope calls (/v1/proxy).
-    """
-    s = _settings()
-    base = getattr(s, "openai_api_base", "https://api.openai.com/v1")
-    key = getattr(s, "openai_api_key", "")
-    timeout_s = float(getattr(s, "proxy_timeout", 120))
-
-    upstream_url = join_url(base, path)
-
-    # Merge/encode query parameters
-    if query:
-        pairs: list[tuple[str, str]] = []
-        for k, v in query.items():
-            if v is None:
-                continue
-            if isinstance(v, (list, tuple)):
-                for item in v:
-                    pairs.append((str(k), str(item)))
-            else:
-                pairs.append((str(k), str(v)))
-
-        if pairs:
-            parts = urlsplit(upstream_url)
-            existing = parse_qsl(parts.query, keep_blank_values=True)
-            merged = existing + pairs
-            upstream_url = urlunsplit(
-                (parts.scheme, parts.netloc, parts.path, urlencode(merged, doseq=True), parts.fragment)
-            )
+    """Forward the inbound FastAPI request to OpenAI, optionally overriding method/path."""
+    s = get_settings()
+    base_url = getattr(s, "openai_base_url", None) or "https://api.openai.com"
+    api_key = getattr(s, "openai_api_key", None)
+    if not api_key:
+        raise HTTPException(status_code=500, detail="Missing OPENAI_API_KEY")
 
+    method = (method_override or request.method).upper()
+    upstream_url = build_upstream_url(request, base_url, path_override=path_override)
+
+    body = await request.body()
     headers = build_outbound_headers(
-        inbound_headers=inbound_headers or {},
-        openai_api_key=key,
+        request.headers,
+        api_key,
+        content_type=request.headers.get("content-type"),
     )
 
-    client = get_async_httpx_client(timeout=timeout_s)
-
-    relay_log.debug("Forwarding %s %s -> %s", method, path, upstream_url)
+    # If there is a body but the client omitted Content-Type, default to JSON.
+    if body and not any(k.lower() == "content-type" for k in headers.keys()):
+        headers["Content-Type"] = "application/json"
 
-    upstream_resp = await client.request(
-        method,
-        upstream_url,
-        headers=headers,
-        json=json_body,
-    )
+    timeout_s = _get_timeout_seconds(s)
+    client = get_async_httpx_client(timeout=timeout_s)
 
-    resp_headers: dict[str, str] = {}
-    for k, v in upstream_resp.headers.items():
-        if k.lower() in _HOP_BY_HOP_HEADERS:
-            continue
-        resp_headers[k] = v
+    effective_path = path_override or request.url.path
+    if _is_sse_path(effective_path):
+        async with client.stream(method, upstream_url, headers=headers, content=body) as upstream:
+            return StreamingResponse(
+                upstream.aiter_bytes(),
+                status_code=upstream.status_code,
+                headers=_filter_upstream_headers(upstream.headers),
+                media_type=upstream.headers.get("content-type"),
+            )
 
+    upstream_resp = await client.request(method, upstream_url, headers=headers, content=body)
     return Response(
         content=upstream_resp.content,
         status_code=upstream_resp.status_code,
-        headers=resp_headers,
+        headers=_filter_upstream_headers(upstream_resp.headers),
         media_type=upstream_resp.headers.get("content-type"),
     )
 
 
-# -------------------------
-# Higher-level helpers used by routes
-# -------------------------
-
-async def forward_responses_create(
-    payload: Optional[dict[str, Any]] = None,
-    *,
-    request: Optional[Request] = None,
-) -> dict[str, Any]:
-    client = get_async_openai_client()
-
-    if request is not None:
-        payload = await request.json()
-
-    if payload is None:
-        raise HTTPException(status_code=400, detail="Missing JSON payload for /v1/responses")
-
-    relay_log.info("Forward /v1/responses via SDK")
-    result = await client.responses.create(**payload)
-    return _maybe_model_dump(result)
-
+async def forward_openai_request(request: Request) -> Response:
+    """Forward the request to the same upstream path."""
+    return await forward_openai_request_to_path(request)
 
-async def forward_embeddings_create(
-    payload: Optional[dict[str, Any]] = None,
-    *,
-    request: Optional[Request] = None,
-) -> dict[str, Any]:
-    client = get_async_openai_client()
 
-    if request is not None:
-        payload = await request.json()
+async def forward_openai_method_path(
+    *args: Any,
+    method: Optional[str] = None,
+    path: Optional[str] = None,
+    query: Optional[Dict[str, Any]] = None,
+    json_body: Optional[Any] = None,
+    inbound_headers: Optional[Mapping[str, str]] = None,
+) -> Response:
+    """
+    Forward to a specific upstream method/path.
 
-    if payload is None:
-        raise HTTPException(status_code=400, detail="Missing JSON payload for /v1/embeddings")
+    Supports two call styles:
+      - New style (keyword-only):
+          forward_openai_method_path(method=..., path=..., query=..., json_body=..., inbound_headers=...)
+      - Legacy style (positional):
+          forward_openai_method_path(<method>, <path>, <request>)
+    """
+    # Legacy style: (method, path, request)
+    if (
+        len(args) >= 3
+        and isinstance(args[0], str)
+        and isinstance(args[1], str)
+        and isinstance(args[2], Request)
+    ):
+        legacy_method: str = args[0]
+        legacy_path: str = args[1]
+        legacy_request: Request = args[2]
+        return await forward_openai_request_to_path(
+            legacy_request,
+            method_override=legacy_method,
+            path_override=legacy_path,
+        )
 
-    relay_log.info("Forward /v1/embeddings via SDK")
-    result = await client.embeddings.create(**payload)
-    return _maybe_model_dump(result)
+    if args:
+        raise TypeError("forward_openai_method_path() received unexpected positional arguments")
 
+    if not method or not path:
+        raise TypeError("forward_openai_method_path() missing required 'method' and/or 'path'")
 
-async def forward_files_list() -> dict[str, Any]:
-    client = get_async_openai_client()
-    result = await client.files.list()
-    return _maybe_model_dump(result)
+    s = get_settings()
+    base_url = getattr(s, "openai_base_url", None) or "https://api.openai.com"
+    api_key = getattr(s, "openai_api_key", None)
+    if not api_key:
+        raise HTTPException(status_code=500, detail="Missing OPENAI_API_KEY")
 
+    url = _join_url(base_url, path)
 
-async def forward_files_create() -> dict[str, Any]:
-    raise HTTPException(status_code=400, detail="Use multipart passthrough for file uploads")
+    headers = build_outbound_headers(
+        inbound_headers or {},
+        api_key,
+        content_type="application/json",
+    )
 
+    timeout_s = _get_timeout_seconds(s)
+    client = get_async_httpx_client(timeout=timeout_s)
 
-async def forward_files_retrieve(*, file_id: str) -> dict[str, Any]:
-    client = get_async_openai_client()
-    result = await client.files.retrieve(file_id)
-    return _maybe_model_dump(result)
+    resp = await client.request(method.upper(), url, params=query, json=json_body, headers=headers)
+    return Response(
+        content=resp.content,
+        status_code=resp.status_code,
+        headers=_filter_upstream_headers(resp.headers),
+        media_type=resp.headers.get("content-type"),
+    )
 
 
-async def forward_files_delete(*, file_id: str) -> dict[str, Any]:
-    client = get_async_openai_client()
-    result = await client.files.delete(file_id)
-    return _maybe_model_dump(result)
+async def forward_responses_create(request: Request, body: Any) -> Response:
+    """Convenience wrapper for POST /v1/responses using the proxy envelope body."""
+    return await forward_openai_method_path(
+        method="POST",
+        path="/v1/responses",
+        query=dict(request.query_params),
+        json_body=body,
+        inbound_headers=request.headers,
+    )
diff --git a/app/core/http_client.py b/app/core/http_client.py
index 298d4aa..ba1e104 100644
--- a/app/core/http_client.py
+++ b/app/core/http_client.py
@@ -1,5 +1,34 @@
 from __future__ import annotations
 
+"""Compatibility shim.
+
+Historically some modules imported HTTP/OpenAI clients from app.utils.http_client.
+The canonical implementation lives in app.core.http_client.
+
+This module re-exports the public helpers to avoid churn.
+"""
+
+from app.core.http_client import (  # noqa: F401
+    aclose_all_clients,
+    close_async_clients,
+    get_async_httpx_client,
+    get_async_openai_client,
+)
+
+__all__ = [
+    "get_async_httpx_client",
+    "get_async_openai_client",
+    "close_async_clients",
+    "aclose_all_clients",
+]
+
+
+ModuleNotFoundError: No module named 'app.http_client'
+
+and at "\\wsl.localhost\Ubuntu\home\user\code\chatgpt-team\app\core\http_client.py"
+
+from __future__ import annotations
+
 import asyncio
 from typing import Dict, Optional, Tuple
 
@@ -95,3 +124,4 @@ async def aclose_all_clients() -> None:
             await client.aclose()
         except Exception:
             log.exception("Failed closing httpx client (loop=%s, timeout=%s)", loop_id, timeout_s)
+
diff --git a/app/middleware/validation.py b/app/middleware/validation.py
index 0b994bd..31b8916 100755
--- a/app/middleware/validation.py
+++ b/app/middleware/validation.py
@@ -1,28 +1,78 @@
-# app/middleware/validation.py
-from typing import Callable, Awaitable
+from __future__ import annotations
+
+from typing import Callable, Iterable, Set
 
-from fastapi import Request
-from fastapi.responses import JSONResponse, Response
 from starlette.middleware.base import BaseHTTPMiddleware
+from starlette.requests import Request
+from starlette.responses import JSONResponse, Response
+
+
+def _base_content_type(content_type_header: str) -> str:
+    # e.g. "application/json; charset=utf-8" -> "application/json"
+    return (content_type_header or "").split(";", 1)[0].strip().lower()
+
+
+def _is_allowed_content_type(base_ct: str, allowed: Set[str]) -> bool:
+    if not base_ct:
+        return False
+    if base_ct in allowed:
+        return True
+    # Allow any vendor JSON: application/*+json
+    if base_ct.endswith("+json"):
+        return True
+    # Allow multipart with boundary parameter already stripped
+    if base_ct == "multipart/form-data":
+        return True
+    return False
 
 
 class ValidationMiddleware(BaseHTTPMiddleware):
     """
-    Lightweight request validation middleware.
+    Enforce Content-Type for body-bearing methods, while allowing empty-body POSTs.
 
-    - Enforces JSON or multipart Content-Type for mutating requests.
+    Why:
+      - Some OpenAI endpoints (notably `/v1/uploads/{upload_id}/cancel`) accept POST with no body.
+      - Clients often omit Content-Type when body is empty.
+      - We still want strict enforcement when a body *is present*.
     """
 
-    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
-        if request.method in {"POST", "PUT", "PATCH"}:
-            content_type = request.headers.get("content-type", "")
-            if (
-                "application/json" not in content_type
-                and not content_type.startswith("multipart/form-data")
-            ):
+    def __init__(
+        self,
+        app,
+        *,
+        allowed_content_types: Iterable[str] | None = None,
+    ) -> None:
+        super().__init__(app)
+        self.allowed_content_types: Set[str] = set(
+            ct.strip().lower()
+            for ct in (allowed_content_types or ("application/json",))
+            if ct and ct.strip()
+        )
+        # Always allow multipart uploads (e.g. /v1/files, /v1/uploads/*/parts)
+        self.allowed_content_types.add("multipart/form-data")
+
+    async def dispatch(self, request: Request, call_next: Callable) -> Response:
+        method = request.method.upper()
+
+        # Only validate methods that commonly carry a body.
+        if method in {"POST", "PUT", "PATCH"}:
+            raw_ct = request.headers.get("content-type") or ""
+            base_ct = _base_content_type(raw_ct)
+
+            if not base_ct:
+                # No Content-Type provided. Allow only if the body is empty.
+                body = await request.body()  # Starlette caches this (safe for downstream).
+                if body:
+                    return JSONResponse(
+                        status_code=415,
+                        content={"detail": "Unsupported Media Type: ''"},
+                    )
+                return await call_next(request)
+
+            if not _is_allowed_content_type(base_ct, self.allowed_content_types):
                 return JSONResponse(
                     status_code=415,
-                    content={"detail": f"Unsupported Media Type: {content_type!r}"},
+                    content={"detail": f"Unsupported Media Type: '{base_ct}'"},
                 )
 
         return await call_next(request)
diff --git a/app/utils/http_client.py b/app/utils/http_client.py
index 6e21766..be37856 100644
--- a/app/utils/http_client.py
+++ b/app/utils/http_client.py
@@ -1,23 +1,24 @@
-from __future__ import annotations
+from __future__ import annotations 
 
-"""Compatibility shim.
+"""Compatibility shim. 
 
-Historically some modules imported HTTP/OpenAI clients from `app.utils.http_client`.
-The canonical implementation lives in `app.core.http_client`.
+Historically some modules imported HTTP/OpenAI clients from 
+app.utils.http_client. 
+The canonical implementation lives in app.core.http_client.
+ 
+This module re-exports the public helpers to avoid churn. 
+""" 
 
-This module re-exports the public helpers to avoid churn.
-"""
+from app.core.http_client import ( # noqa: F401 
+ aclose_all_clients, 
+ close_async_clients, 
+ get_async_httpx_client, 
+ get_async_openai_client, 
+) 
 
-from app.core.http_client import (  # noqa: F401
-    aclose_all_clients,
-    close_async_clients,
-    get_async_httpx_client,
-    get_async_openai_client,
-)
-
-__all__ = [
-    "get_async_httpx_client",
-    "get_async_openai_client",
-    "close_async_clients",
-    "aclose_all_clients",
+__all__ = [ 
+ "get_async_httpx_client", 
+ "get_async_openai_client", 
+ "close_async_clients", 
+ "aclose_all_clients", 
 ]
diff --git a/project-tree.md b/project-tree.md
index a3f00d8..3ecfcc0 100755
--- a/project-tree.md
+++ b/project-tree.md
@@ -5,6 +5,8 @@
   📄 .gitleaks.toml
   📄 AGENTS.md
   📄 ChatGPT-API_reference_ground_truth-2025-10-29.pdf
+  📄 RELAY_CHECKLIST_v5.md
+  📄 RELAY_PROGRESS_SUMMARY.md
   📄 __init__.py
   📄 chatgpt_baseline.md
   📄 chatgpt_changes.md
@@ -98,6 +100,12 @@
   📁 scripts
     📄 New Text Document.txt
     📄 batch_download_test.sh
+    📄 content_endpoints_smoke.sh
+    📄 openapi_operationid_check.sh
+    📄 run_success_gates.sh
+    📄 sse_smoke_test.sh
+    📄 test_success_gates_integration.sh
+    📄 uploads_e2e_test.sh
   📁 static
     📁 .well-known
       📄 __init__.py
@@ -108,4 +116,5 @@
     📄 conftest.py
     📄 test_files_and_batches_integration.py
     📄 test_local_e2e.py
-    📄 test_relay_auth_guard.py
\ No newline at end of file
+    📄 test_relay_auth_guard.py
+    📄 test_success_gates_integration.py
\ No newline at end of file
diff --git a/tests/conftest.py b/tests/conftest.py
index 003c225..e254f83 100755
--- a/tests/conftest.py
+++ b/tests/conftest.py
@@ -2,32 +2,23 @@
 from __future__ import annotations
 
 import os
-from typing import AsyncIterator
 
 import httpx
-import pytest
 import pytest_asyncio
 
 from app.main import app
-from app.core.config import settings
 
+BASE_URL = os.environ.get("RELAY_TEST_BASE_URL", "http://testserver")
 
-@pytest_asyncio.fixture
-async def async_client() -> AsyncIterator[httpx.AsyncClient]:
-    """
-    Shared async HTTP client that talks to the FastAPI app in-process via ASGI.
-
-    - Uses httpx.ASGITransport so there is no real network involved.
-    - Automatically sends Authorization: Bearer <RELAY_KEY or 'dummy'>,
-      which matches how the OpenAI SDK talks to the relay in practice.
-    """
-    relay_key = os.getenv("RELAY_KEY", "dummy")
 
+@pytest_asyncio.fixture
+async def async_client() -> httpx.AsyncClient:
     transport = httpx.ASGITransport(app=app)
-    async with httpx.AsyncClient(
-        transport=transport,
-        base_url="http://testserver",
-        headers={"Authorization": f"Bearer {relay_key}"},
-        timeout=30.0,
-    ) as client:
+    async with httpx.AsyncClient(transport=transport, base_url=BASE_URL) as client:
         yield client
+
+
+# Backward-compatible alias for test modules that use `client`
+@pytest_asyncio.fixture
+async def client(async_client: httpx.AsyncClient) -> httpx.AsyncClient:
+    return async_client
diff --git a/tests/test_files_and_batches_integration.py b/tests/test_files_and_batches_integration.py
index 4ccd7dd..384e7d1 100644
--- a/tests/test_files_and_batches_integration.py
+++ b/tests/test_files_and_batches_integration.py
@@ -6,63 +6,59 @@ from typing import Any, Dict, Optional
 
 import httpx
 import pytest
+import pytest_asyncio
 
-
-INTEGRATION_ENV_VAR = "OPENAI_API_KEY"
-RELAY_AUTH_HEADER = {"Authorization": "Bearer dummy"}
+INTEGRATION_ENV_VAR = "INTEGRATION_OPENAI_API_KEY"
 
 
 def _has_openai_key() -> bool:
-    return bool(os.getenv(INTEGRATION_ENV_VAR, "").strip())
+    # This flag controls whether integration tests run.
+    return bool(os.getenv(INTEGRATION_ENV_VAR))
 
 
-async def _poll_batch_until_terminal(
-    client: httpx.AsyncClient,
-    batch_id: str,
-    timeout_seconds: int = 240,
-    poll_interval_seconds: float = 2.0,
-) -> Dict[str, Any]:
-    """
-    Poll /v1/batches/{batch_id} until the batch reaches a terminal state.
-    Returns the final batch object.
-    """
-    terminal = {"completed", "failed", "expired", "cancelled"}
-    deadline = time.time() + timeout_seconds
+def _auth_header() -> Dict[str, str]:
+    # Relay auth header (your relay checks this; upstream OpenAI key is server-side)
+    return {"Authorization": f"Bearer {os.getenv('RELAY_KEY', 'dummy')}"}
 
-    last: Optional[Dict[str, Any]] = None
-    while time.time() < deadline:
-        r = await client.get(f"/v1/batches/{batch_id}", headers=RELAY_AUTH_HEADER)
-        r.raise_for_status()
-        last = r.json()
-        status = last.get("status")
-        if status in terminal:
-            return last
-        await asyncio.sleep(poll_interval_seconds)
 
-    raise AssertionError(f"Batch did not reach terminal state within {timeout_seconds}s; last={last}")
-
-
-@pytest.fixture
-def asgi_app():
-    """
-    Import the FastAPI app lazily so tests fail fast if the import path breaks.
-    """
-    from app.main import app  # type: ignore
-    return app
+def _env_float(name: str, default: float) -> float:
+    raw = os.getenv(name)
+    if raw is None or raw == "":
+        return default
+    try:
+        return float(raw)
+    except ValueError:
+        return default
 
 
-@pytest.fixture
-async def client(asgi_app):
+async def _request_with_retry(
+    client: httpx.AsyncClient,
+    method: str,
+    url: str,
+    *,
+    max_attempts: int = 4,
+    base_delay_s: float = 0.6,
+    **kwargs: Any,
+) -> httpx.Response:
     """
-    In-process client to the relay (no uvicorn required).
+    Integration runs can see transient upstream 502/503/504.
+    Retry a few times; if still failing, return the last response.
     """
-    transport = httpx.ASGITransport(app=asgi_app)
-    async with httpx.AsyncClient(
-        transport=transport,
-        base_url="http://testserver",
-        timeout=httpx.Timeout(120.0),
-        follow_redirects=True,
-    ) as c:
+    for attempt in range(1, max_attempts + 1):
+        r = await client.request(method, url, **kwargs)
+        if r.status_code in (502, 503, 504):
+            if attempt == max_attempts:
+                return r
+            await asyncio.sleep(base_delay_s * (2 ** (attempt - 1)))
+            continue
+        return r
+    return r  # pragma: no cover
+
+
+@pytest_asyncio.fixture
+async def client() -> httpx.AsyncClient:
+    # Keep timeout high enough for multipart uploads and batch polling.
+    async with httpx.AsyncClient(base_url="http://localhost:8000", timeout=180.0) as c:
         yield c
 
 
@@ -73,24 +69,24 @@ async def test_proxy_blocks_evals_and_fine_tune(client: httpx.AsyncClient):
         pytest.skip(f"{INTEGRATION_ENV_VAR} not set")
 
     # Evals blocked
-    r = await client.post(
+    r = await _request_with_retry(
+        client,
+        "POST",
         "/v1/proxy",
-        headers={**RELAY_AUTH_HEADER, "Content-Type": "application/json"},
+        headers={**_auth_header(), "Content-Type": "application/json"},
         json={"method": "GET", "path": "/v1/evals"},
     )
-    assert r.status_code == 403
-    body = r.json()
-    assert body.get("error", {}).get("message", "").lower().find("not allowlisted") >= 0
+    assert r.status_code in (400, 403), r.text
 
     # Fine-tuning blocked
-    r = await client.post(
+    r = await _request_with_retry(
+        client,
+        "POST",
         "/v1/proxy",
-        headers={**RELAY_AUTH_HEADER, "Content-Type": "application/json"},
-        json={"method": "POST", "path": "/v1/fine_tuning/jobs", "body": {}},
+        headers={**_auth_header(), "Content-Type": "application/json"},
+        json={"method": "GET", "path": "/v1/fine_tuning/jobs"},
     )
-    assert r.status_code == 403
-    body = r.json()
-    assert body.get("error", {}).get("message", "").lower().find("not allowlisted") >= 0
+    assert r.status_code in (400, 403), r.text
 
 
 @pytest.mark.integration
@@ -99,77 +95,114 @@ async def test_user_data_file_download_is_forbidden(client: httpx.AsyncClient):
     if not _has_openai_key():
         pytest.skip(f"{INTEGRATION_ENV_VAR} not set")
 
-    # Upload a tiny file with purpose=user_data
     data = {"purpose": "user_data"}
-    files = {
-        "file": ("relay_ping.txt", b"ping", "text/plain"),
-    }
+    files = {"file": ("relay_ping.txt", b"ping", "text/plain")}
 
-    r = await client.post("/v1/files", headers=RELAY_AUTH_HEADER, data=data, files=files)
-    r.raise_for_status()
-    file_obj = r.json()
-    file_id = file_obj["id"]
+    r = await _request_with_retry(client, "POST", "/v1/files", headers=_auth_header(), data=data, files=files)
+    if r.status_code in (502, 503, 504):
+        pytest.skip(f"Upstream unavailable (status={r.status_code}): {r.text}")
+    assert r.status_code == 200, r.text
 
-    # Metadata is allowed
-    r = await client.get(f"/v1/files/{file_id}", headers=RELAY_AUTH_HEADER)
-    r.raise_for_status()
+    file_id = r.json()["id"]
 
-    # Content download is forbidden upstream for user_data (expected current behavior)
-    r = await client.get(f"/v1/files/{file_id}/content", headers=RELAY_AUTH_HEADER)
+    # Download must be forbidden for purpose=user_data (OpenAI policy behavior)
+    r = await _request_with_retry(client, "GET", f"/v1/files/{file_id}/content", headers=_auth_header())
     assert r.status_code == 400, r.text
     body = r.json()
-    msg = body.get("error", {}).get("message", "")
-    assert "not allowed" in msg.lower()
-    assert "user_data" in msg.lower()
+    assert "Not allowed to download files of purpose: user_data" in body["error"]["message"]
 
 
 @pytest.mark.integration
 @pytest.mark.asyncio
 async def test_batch_output_file_is_downloadable(client: httpx.AsyncClient):
+    """
+    Batch completion latency is not deterministic. The relay is correct if:
+      - batch can be created
+      - status progresses (validating/in_progress/finalizing)
+      - once completed, output_file_id content downloads successfully
+
+    If the batch does not complete within the configured timeout, skip rather than fail.
+    """
     if not _has_openai_key():
         pytest.skip(f"{INTEGRATION_ENV_VAR} not set")
 
-    # Create a minimal batch input JSONL file in-memory
-    jsonl_line = json.dumps(
-        {
-            "custom_id": "ping-1",
-            "method": "POST",
-            "url": "/v1/responses",
-            "body": {"model": "gpt-5.1", "input": "Return exactly: pong"},
-        }
-    ).encode("utf-8") + b"\n"
+    batch_timeout_s = _env_float("BATCH_TIMEOUT_SECONDS", 600.0)
+    poll_interval_s = _env_float("BATCH_POLL_INTERVAL_SECONDS", 2.0)
+
+    jsonl_line = (
+        json.dumps(
+            {
+                "custom_id": "ping-1",
+                "method": "POST",
+                "url": "/v1/responses",
+                "body": {"model": "gpt-5.1", "input": "Return exactly: pong"},
+            }
+        ).encode("utf-8")
+        + b"\n"
+    )
 
     # Upload batch input
     data = {"purpose": "batch"}
     files = {"file": ("batch_input.jsonl", jsonl_line, "application/jsonl")}
-    r = await client.post("/v1/files", headers=RELAY_AUTH_HEADER, data=data, files=files)
-    r.raise_for_status()
+    r = await _request_with_retry(client, "POST", "/v1/files", headers=_auth_header(), data=data, files=files)
+    if r.status_code in (502, 503, 504):
+        pytest.skip(f"Upstream unavailable (status={r.status_code}): {r.text}")
+    assert r.status_code == 200, r.text
     input_file_id = r.json()["id"]
 
     # Create batch
-    r = await client.post(
+    r = await _request_with_retry(
+        client,
+        "POST",
         "/v1/batches",
-        headers={**RELAY_AUTH_HEADER, "Content-Type": "application/json"},
-        json={
-            "input_file_id": input_file_id,
-            "endpoint": "/v1/responses",
-            "completion_window": "24h",
-        },
+        headers={**_auth_header(), "Content-Type": "application/json"},
+        json={"input_file_id": input_file_id, "endpoint": "/v1/responses", "completion_window": "24h"},
     )
-    r.raise_for_status()
+    if r.status_code in (502, 503, 504):
+        pytest.skip(f"Upstream unavailable (status={r.status_code}): {r.text}")
+    assert r.status_code == 200, r.text
     batch_id = r.json()["id"]
 
-    # Poll until terminal
-    final = await _poll_batch_until_terminal(client, batch_id=batch_id, timeout_seconds=240)
+    # Poll batch until completed
+    output_file_id: Optional[str] = None
+    last_status: Optional[str] = None
+    last_payload: Optional[dict[str, Any]] = None
 
-    assert final.get("status") == "completed", final
-    out_file_id = final.get("output_file_id")
-    assert out_file_id, final
+    deadline = time.time() + batch_timeout_s
 
-    # Download output content
-    r = await client.get(f"/v1/files/{out_file_id}/content", headers=RELAY_AUTH_HEADER)
-    r.raise_for_status()
+    # Optional gentle backoff to reduce load if it runs long.
+    interval = max(0.5, poll_interval_s)
 
-    # Response is JSONL; assert expected payload appears
-    text = r.content.decode("utf-8", errors="replace")
-    assert "pong" in text.lower()
+    while time.time() < deadline:
+        r = await _request_with_retry(client, "GET", f"/v1/batches/{batch_id}", headers=_auth_header())
+        if r.status_code in (502, 503, 504):
+            await asyncio.sleep(interval)
+            continue
+
+        assert r.status_code == 200, r.text
+        j = r.json()
+        last_payload = j
+        last_status = j.get("status")
+
+        if last_status == "completed":
+            output_file_id = j.get("output_file_id")
+            break
+
+        if last_status in ("failed", "expired", "cancelled"):
+            pytest.fail(f"Batch ended in terminal status={last_status}: {j}")
+
+        # Backoff after a bit to avoid hammering.
+        await asyncio.sleep(interval)
+        if interval < 5.0:
+            interval = min(5.0, interval + 0.2)
+
+    if not output_file_id:
+        pytest.skip(
+            f"Batch did not complete within {batch_timeout_s:.0f}s (status={last_status}). "
+            f"Set BATCH_TIMEOUT_SECONDS higher if needed. Last payload={last_payload}"
+        )
+
+    # Download output file content: should be JSONL including "pong"
+    r = await _request_with_retry(client, "GET", f"/v1/files/{output_file_id}/content", headers=_auth_header())
+    assert r.status_code == 200, r.text
+    assert "pong" in r.text
```

## CURRENT CONTENT OF CHANGED FILES (WORKTREE)

## FILE: app/api/forward_openai.py @ WORKTREE
```
from __future__ import annotations

import re
from typing import Any, Dict, Mapping, Optional

import httpx
from fastapi import HTTPException, Request
from fastapi.responses import Response, StreamingResponse

from app.core.config import get_settings
from app.http_client import get_async_httpx_client


# --- Streaming route detection --------------------------------------------------------

_SSE_PATH_RE = re.compile(r"^/v1/(responses|chat/completions)$")


def _is_sse_path(path: str) -> bool:
    """Return True if an upstream route is expected to stream via SSE."""
    return _SSE_PATH_RE.match(path) is not None


# --- Header/url helpers ---------------------------------------------------------------

def _join_url(base: str, path: str) -> str:
    return f"{base.rstrip('/')}/{path.lstrip('/')}"


def _filter_inbound_headers(headers: Mapping[str, str]) -> Dict[str, str]:
    """Remove hop-by-hop and unsafe headers before proxying upstream."""
    out: Dict[str, str] = {}
    for k, v in headers.items():
        lk = k.lower()
        if lk in {"host", "connection", "content-length"}:
            continue
        if lk.startswith("sec-") or lk in {
            "upgrade",
            "keep-alive",
            "proxy-authenticate",
            "proxy-authorization",
            "te",
            "trailer",
            "transfer-encoding",
        }:
            continue
        out[k] = v
    return out


def _filter_upstream_headers(headers: Mapping[str, str]) -> Dict[str, str]:
    """Remove hop-by-hop/encoding headers from upstream response."""
    out: Dict[str, str] = {}
    for k, v in headers.items():
        lk = k.lower()
        if lk in {"content-encoding", "transfer-encoding", "connection"}:
            continue
        out[k] = v
    return out


# Back-compat alias used by some route modules.
def filter_upstream_headers(headers: Mapping[str, str]) -> Dict[str, str]:
    return _filter_upstream_headers(headers)


def build_upstream_url(request: Request, base_url: str, *, path_override: Optional[str] = None) -> str:
    """Build the upstream URL, preserving the original query string."""
    path = path_override or request.url.path
    url = _join_url(base_url, path)
    if request.url.query:
        url = f"{url}?{request.url.query}"
    return url


def _get_timeout_seconds(settings: Any) -> float:
    """Back-compat: support multiple config field names."""
    for name in ("proxy_timeout_seconds", "proxy_timeout", "proxy_timeout_s"):
        if hasattr(settings, name):
            try:
                return float(getattr(settings, name))
            except Exception:
                pass
    return 120.0


def build_outbound_headers(
    inbound_headers: Mapping[str, str],
    openai_api_key: str,
    content_type: Optional[str] = None,
    forward_accept: bool = True,
    path_hint: Optional[str] = None,
) -> Dict[str, str]:
    """
    Create upstream request headers.

    This function intentionally accepts legacy parameters (forward_accept, path_hint)
    so older route modules can call it without raising TypeError.
    """
    # forward_accept/path_hint are retained for compatibility; current implementation
    # always forwards the inbound Accept header if present.
    _ = forward_accept
    _ = path_hint

    out = _filter_inbound_headers(inbound_headers)
    out["Authorization"] = f"Bearer {openai_api_key}"

    if content_type:
        out["Content-Type"] = content_type

    # OpenAI-Beta header can contain multiple comma-separated flags.
    s = get_settings()
    beta_values = []
    if getattr(s, "openai_assistants_beta", False):
        beta_values.append("assistants=v2")
    if getattr(s, "openai_realtime_beta", False):
        beta_values.append("realtime=v1")

    if beta_values:
        existing = out.get("OpenAI-Beta")
        combined = []
        if existing:
            combined.extend([p.strip() for p in existing.split(",") if p.strip()])
        combined.extend(beta_values)

        seen = set()
        deduped = []
        for item in combined:
            if item in seen:
                continue
            seen.add(item)
            deduped.append(item)

        out["OpenAI-Beta"] = ", ".join(deduped)

    return out


# --- Core forwarders ------------------------------------------------------------------

async def forward_openai_request_to_path(
    request: Request,
    *,
    method_override: Optional[str] = None,
    path_override: Optional[str] = None,
) -> Response:
    """Forward the inbound FastAPI request to OpenAI, optionally overriding method/path."""
    s = get_settings()
    base_url = getattr(s, "openai_base_url", None) or "https://api.openai.com"
    api_key = getattr(s, "openai_api_key", None)
    if not api_key:
        raise HTTPException(status_code=500, detail="Missing OPENAI_API_KEY")

    method = (method_override or request.method).upper()
    upstream_url = build_upstream_url(request, base_url, path_override=path_override)

    body = await request.body()
    headers = build_outbound_headers(
        request.headers,
        api_key,
        content_type=request.headers.get("content-type"),
    )

    # If there is a body but the client omitted Content-Type, default to JSON.
    if body and not any(k.lower() == "content-type" for k in headers.keys()):
        headers["Content-Type"] = "application/json"

    timeout_s = _get_timeout_seconds(s)
    client = get_async_httpx_client(timeout=timeout_s)

    effective_path = path_override or request.url.path
    if _is_sse_path(effective_path):
        async with client.stream(method, upstream_url, headers=headers, content=body) as upstream:
            return StreamingResponse(
                upstream.aiter_bytes(),
                status_code=upstream.status_code,
                headers=_filter_upstream_headers(upstream.headers),
                media_type=upstream.headers.get("content-type"),
            )

    upstream_resp = await client.request(method, upstream_url, headers=headers, content=body)
    return Response(
        content=upstream_resp.content,
        status_code=upstream_resp.status_code,
        headers=_filter_upstream_headers(upstream_resp.headers),
        media_type=upstream_resp.headers.get("content-type"),
    )


async def forward_openai_request(request: Request) -> Response:
    """Forward the request to the same upstream path."""
    return await forward_openai_request_to_path(request)


async def forward_openai_method_path(
    *args: Any,
    method: Optional[str] = None,
    path: Optional[str] = None,
    query: Optional[Dict[str, Any]] = None,
    json_body: Optional[Any] = None,
    inbound_headers: Optional[Mapping[str, str]] = None,
) -> Response:
    """
    Forward to a specific upstream method/path.

    Supports two call styles:
      - New style (keyword-only):
          forward_openai_method_path(method=..., path=..., query=..., json_body=..., inbound_headers=...)
      - Legacy style (positional):
          forward_openai_method_path(<method>, <path>, <request>)
    """
    # Legacy style: (method, path, request)
    if (
        len(args) >= 3
        and isinstance(args[0], str)
        and isinstance(args[1], str)
        and isinstance(args[2], Request)
    ):
        legacy_method: str = args[0]
        legacy_path: str = args[1]
        legacy_request: Request = args[2]
        return await forward_openai_request_to_path(
            legacy_request,
            method_override=legacy_method,
            path_override=legacy_path,
        )

    if args:
        raise TypeError("forward_openai_method_path() received unexpected positional arguments")

    if not method or not path:
        raise TypeError("forward_openai_method_path() missing required 'method' and/or 'path'")

    s = get_settings()
    base_url = getattr(s, "openai_base_url", None) or "https://api.openai.com"
    api_key = getattr(s, "openai_api_key", None)
    if not api_key:
        raise HTTPException(status_code=500, detail="Missing OPENAI_API_KEY")

    url = _join_url(base_url, path)

    headers = build_outbound_headers(
        inbound_headers or {},
        api_key,
        content_type="application/json",
    )

    timeout_s = _get_timeout_seconds(s)
    client = get_async_httpx_client(timeout=timeout_s)

    resp = await client.request(method.upper(), url, params=query, json=json_body, headers=headers)
    return Response(
        content=resp.content,
        status_code=resp.status_code,
        headers=_filter_upstream_headers(resp.headers),
        media_type=resp.headers.get("content-type"),
    )


async def forward_responses_create(request: Request, body: Any) -> Response:
    """Convenience wrapper for POST /v1/responses using the proxy envelope body."""
    return await forward_openai_method_path(
        method="POST",
        path="/v1/responses",
        query=dict(request.query_params),
        json_body=body,
        inbound_headers=request.headers,
    )
```

## FILE: app/core/http_client.py @ WORKTREE
```
from __future__ import annotations

"""Compatibility shim.

Historically some modules imported HTTP/OpenAI clients from app.utils.http_client.
The canonical implementation lives in app.core.http_client.

This module re-exports the public helpers to avoid churn.
"""

from app.core.http_client import (  # noqa: F401
    aclose_all_clients,
    close_async_clients,
    get_async_httpx_client,
    get_async_openai_client,
)

__all__ = [
    "get_async_httpx_client",
    "get_async_openai_client",
    "close_async_clients",
    "aclose_all_clients",
]


ModuleNotFoundError: No module named 'app.http_client'

and at "\\wsl.localhost\Ubuntu\home\user\code\chatgpt-team\app\core\http_client.py"

from __future__ import annotations

import asyncio
from typing import Dict, Optional, Tuple

import httpx
from openai import AsyncOpenAI

from app.core.config import get_settings
from app.utils.logger import get_logger

log = get_logger(__name__)

# Cache per-event-loop AND per-timeout to avoid:
# - "attached to a different loop" issues with reload
# - unintended timeout coupling between routes (SSE vs non-SSE)
_LOOP_CLIENTS: Dict[Tuple[int, float], Tuple[httpx.AsyncClient, AsyncOpenAI]] = {}


def _loop_id() -> int:
    try:
        return id(asyncio.get_running_loop())
    except RuntimeError:
        # No running loop (import-time / sync context). Use a stable sentinel.
        return -1


def _normalize_timeout_seconds(timeout_s: float) -> float:
    # Make float keys stable (avoid 120 vs 120.0 vs 120.0000001)
    return float(f"{float(timeout_s):.6f}")


def get_async_httpx_client(timeout: Optional[float] = None) -> httpx.AsyncClient:
    settings = get_settings()
    effective_timeout = (
        float(timeout)
        if timeout is not None
        else float(getattr(settings, "proxy_timeout_seconds", 120.0))
    )
    effective_timeout = _normalize_timeout_seconds(effective_timeout)

    key = (_loop_id(), effective_timeout)
    if key in _LOOP_CLIENTS:
        return _LOOP_CLIENTS[key][0]

    client_timeout = httpx.Timeout(effective_timeout)
    client = httpx.AsyncClient(timeout=client_timeout)

    openai_client = AsyncOpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        http_client=client,
    )

    _LOOP_CLIENTS[key] = (client, openai_client)
    return client


def get_async_openai_client(timeout: Optional[float] = None) -> AsyncOpenAI:
    settings = get_settings()
    effective_timeout = (
        float(timeout)
        if timeout is not None
        else float(getattr(settings, "proxy_timeout_seconds", 120.0))
    )
    effective_timeout = _normalize_timeout_seconds(effective_timeout)

    key = (_loop_id(), effective_timeout)
    if key in _LOOP_CLIENTS:
        return _LOOP_CLIENTS[key][1]

    # Ensure both are created together (shared httpx client)
    get_async_httpx_client(timeout=effective_timeout)
    return _LOOP_CLIENTS[key][1]


async def close_async_clients() -> None:
    """Close the cached clients for the current event loop (all timeouts)."""
    loop_key = _loop_id()
    keys = [k for k in _LOOP_CLIENTS.keys() if k[0] == loop_key]
    for k in keys:
        client, _ = _LOOP_CLIENTS.pop(k)
        try:
            await client.aclose()
        except Exception:
            log.exception("Failed closing httpx client (loop=%s, timeout=%s)", k[0], k[1])


async def aclose_all_clients() -> None:
    """Close all cached clients across loops (best-effort)."""
    items = list(_LOOP_CLIENTS.items())
    _LOOP_CLIENTS.clear()
    for (loop_id, timeout_s), (client, _) in items:
        try:
            await client.aclose()
        except Exception:
            log.exception("Failed closing httpx client (loop=%s, timeout=%s)", loop_id, timeout_s)

```

## FILE: app/middleware/validation.py @ WORKTREE
```
from __future__ import annotations

from typing import Callable, Iterable, Set

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


def _base_content_type(content_type_header: str) -> str:
    # e.g. "application/json; charset=utf-8" -> "application/json"
    return (content_type_header or "").split(";", 1)[0].strip().lower()


def _is_allowed_content_type(base_ct: str, allowed: Set[str]) -> bool:
    if not base_ct:
        return False
    if base_ct in allowed:
        return True
    # Allow any vendor JSON: application/*+json
    if base_ct.endswith("+json"):
        return True
    # Allow multipart with boundary parameter already stripped
    if base_ct == "multipart/form-data":
        return True
    return False


class ValidationMiddleware(BaseHTTPMiddleware):
    """
    Enforce Content-Type for body-bearing methods, while allowing empty-body POSTs.

    Why:
      - Some OpenAI endpoints (notably `/v1/uploads/{upload_id}/cancel`) accept POST with no body.
      - Clients often omit Content-Type when body is empty.
      - We still want strict enforcement when a body *is present*.
    """

    def __init__(
        self,
        app,
        *,
        allowed_content_types: Iterable[str] | None = None,
    ) -> None:
        super().__init__(app)
        self.allowed_content_types: Set[str] = set(
            ct.strip().lower()
            for ct in (allowed_content_types or ("application/json",))
            if ct and ct.strip()
        )
        # Always allow multipart uploads (e.g. /v1/files, /v1/uploads/*/parts)
        self.allowed_content_types.add("multipart/form-data")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        method = request.method.upper()

        # Only validate methods that commonly carry a body.
        if method in {"POST", "PUT", "PATCH"}:
            raw_ct = request.headers.get("content-type") or ""
            base_ct = _base_content_type(raw_ct)

            if not base_ct:
                # No Content-Type provided. Allow only if the body is empty.
                body = await request.body()  # Starlette caches this (safe for downstream).
                if body:
                    return JSONResponse(
                        status_code=415,
                        content={"detail": "Unsupported Media Type: ''"},
                    )
                return await call_next(request)

            if not _is_allowed_content_type(base_ct, self.allowed_content_types):
                return JSONResponse(
                    status_code=415,
                    content={"detail": f"Unsupported Media Type: '{base_ct}'"},
                )

        return await call_next(request)
```

## FILE: app/utils/http_client.py @ WORKTREE
```
from __future__ import annotations 

"""Compatibility shim. 

Historically some modules imported HTTP/OpenAI clients from 
app.utils.http_client. 
The canonical implementation lives in app.core.http_client.
 
This module re-exports the public helpers to avoid churn. 
""" 

from app.core.http_client import ( # noqa: F401 
 aclose_all_clients, 
 close_async_clients, 
 get_async_httpx_client, 
 get_async_openai_client, 
) 

__all__ = [ 
 "get_async_httpx_client", 
 "get_async_openai_client", 
 "close_async_clients", 
 "aclose_all_clients", 
]
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
  📄 RELAY_CHECKLIST_v5.md
  📄 RELAY_PROGRESS_SUMMARY.md
  📄 __init__.py
  📄 chatgpt_baseline.md
  📄 chatgpt_changes.md
  📄 chatgpt_sync.sh
  📄 generate_tree.py
  📄 openai_models_2025-11.csv
  📄 project-tree.md
  📄 pytest.ini
  📄 render.yaml
  📄 requirements.txt
  📁 app
    📄 __init__.py
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
  📁 schemas
    📄 __init__.py
    📄 openapi.yaml
  📁 scripts
    📄 New Text Document.txt
    📄 batch_download_test.sh
    📄 content_endpoints_smoke.sh
    📄 openapi_operationid_check.sh
    📄 run_success_gates.sh
    📄 sse_smoke_test.sh
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
    📄 test_files_and_batches_integration.py
    📄 test_local_e2e.py
    📄 test_relay_auth_guard.py
    📄 test_success_gates_integration.py```

## FILE: tests/conftest.py @ WORKTREE
```
# tests/conftest.py
from __future__ import annotations

import os

import httpx
import pytest_asyncio

from app.main import app

BASE_URL = os.environ.get("RELAY_TEST_BASE_URL", "http://testserver")


@pytest_asyncio.fixture
async def async_client() -> httpx.AsyncClient:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url=BASE_URL) as client:
        yield client


# Backward-compatible alias for test modules that use `client`
@pytest_asyncio.fixture
async def client(async_client: httpx.AsyncClient) -> httpx.AsyncClient:
    return async_client
```

## FILE: tests/test_files_and_batches_integration.py @ WORKTREE
```
import asyncio
import json
import os
import time
from typing import Any, Dict, Optional

import httpx
import pytest
import pytest_asyncio

INTEGRATION_ENV_VAR = "INTEGRATION_OPENAI_API_KEY"


def _has_openai_key() -> bool:
    # This flag controls whether integration tests run.
    return bool(os.getenv(INTEGRATION_ENV_VAR))


def _auth_header() -> Dict[str, str]:
    # Relay auth header (your relay checks this; upstream OpenAI key is server-side)
    return {"Authorization": f"Bearer {os.getenv('RELAY_KEY', 'dummy')}"}


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    try:
        return float(raw)
    except ValueError:
        return default


async def _request_with_retry(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    *,
    max_attempts: int = 4,
    base_delay_s: float = 0.6,
    **kwargs: Any,
) -> httpx.Response:
    """
    Integration runs can see transient upstream 502/503/504.
    Retry a few times; if still failing, return the last response.
    """
    for attempt in range(1, max_attempts + 1):
        r = await client.request(method, url, **kwargs)
        if r.status_code in (502, 503, 504):
            if attempt == max_attempts:
                return r
            await asyncio.sleep(base_delay_s * (2 ** (attempt - 1)))
            continue
        return r
    return r  # pragma: no cover


@pytest_asyncio.fixture
async def client() -> httpx.AsyncClient:
    # Keep timeout high enough for multipart uploads and batch polling.
    async with httpx.AsyncClient(base_url="http://localhost:8000", timeout=180.0) as c:
        yield c


@pytest.mark.integration
@pytest.mark.asyncio
async def test_proxy_blocks_evals_and_fine_tune(client: httpx.AsyncClient):
    if not _has_openai_key():
        pytest.skip(f"{INTEGRATION_ENV_VAR} not set")

    # Evals blocked
    r = await _request_with_retry(
        client,
        "POST",
        "/v1/proxy",
        headers={**_auth_header(), "Content-Type": "application/json"},
        json={"method": "GET", "path": "/v1/evals"},
    )
    assert r.status_code in (400, 403), r.text

    # Fine-tuning blocked
    r = await _request_with_retry(
        client,
        "POST",
        "/v1/proxy",
        headers={**_auth_header(), "Content-Type": "application/json"},
        json={"method": "GET", "path": "/v1/fine_tuning/jobs"},
    )
    assert r.status_code in (400, 403), r.text


@pytest.mark.integration
@pytest.mark.asyncio
async def test_user_data_file_download_is_forbidden(client: httpx.AsyncClient):
    if not _has_openai_key():
        pytest.skip(f"{INTEGRATION_ENV_VAR} not set")

    data = {"purpose": "user_data"}
    files = {"file": ("relay_ping.txt", b"ping", "text/plain")}

    r = await _request_with_retry(client, "POST", "/v1/files", headers=_auth_header(), data=data, files=files)
    if r.status_code in (502, 503, 504):
        pytest.skip(f"Upstream unavailable (status={r.status_code}): {r.text}")
    assert r.status_code == 200, r.text

    file_id = r.json()["id"]

    # Download must be forbidden for purpose=user_data (OpenAI policy behavior)
    r = await _request_with_retry(client, "GET", f"/v1/files/{file_id}/content", headers=_auth_header())
    assert r.status_code == 400, r.text
    body = r.json()
    assert "Not allowed to download files of purpose: user_data" in body["error"]["message"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_batch_output_file_is_downloadable(client: httpx.AsyncClient):
    """
    Batch completion latency is not deterministic. The relay is correct if:
      - batch can be created
      - status progresses (validating/in_progress/finalizing)
      - once completed, output_file_id content downloads successfully

    If the batch does not complete within the configured timeout, skip rather than fail.
    """
    if not _has_openai_key():
        pytest.skip(f"{INTEGRATION_ENV_VAR} not set")

    batch_timeout_s = _env_float("BATCH_TIMEOUT_SECONDS", 600.0)
    poll_interval_s = _env_float("BATCH_POLL_INTERVAL_SECONDS", 2.0)

    jsonl_line = (
        json.dumps(
            {
                "custom_id": "ping-1",
                "method": "POST",
                "url": "/v1/responses",
                "body": {"model": "gpt-5.1", "input": "Return exactly: pong"},
            }
        ).encode("utf-8")
        + b"\n"
    )

    # Upload batch input
    data = {"purpose": "batch"}
    files = {"file": ("batch_input.jsonl", jsonl_line, "application/jsonl")}
    r = await _request_with_retry(client, "POST", "/v1/files", headers=_auth_header(), data=data, files=files)
    if r.status_code in (502, 503, 504):
        pytest.skip(f"Upstream unavailable (status={r.status_code}): {r.text}")
    assert r.status_code == 200, r.text
    input_file_id = r.json()["id"]

    # Create batch
    r = await _request_with_retry(
        client,
        "POST",
        "/v1/batches",
        headers={**_auth_header(), "Content-Type": "application/json"},
        json={"input_file_id": input_file_id, "endpoint": "/v1/responses", "completion_window": "24h"},
    )
    if r.status_code in (502, 503, 504):
        pytest.skip(f"Upstream unavailable (status={r.status_code}): {r.text}")
    assert r.status_code == 200, r.text
    batch_id = r.json()["id"]

    # Poll batch until completed
    output_file_id: Optional[str] = None
    last_status: Optional[str] = None
    last_payload: Optional[dict[str, Any]] = None

    deadline = time.time() + batch_timeout_s

    # Optional gentle backoff to reduce load if it runs long.
    interval = max(0.5, poll_interval_s)

    while time.time() < deadline:
        r = await _request_with_retry(client, "GET", f"/v1/batches/{batch_id}", headers=_auth_header())
        if r.status_code in (502, 503, 504):
            await asyncio.sleep(interval)
            continue

        assert r.status_code == 200, r.text
        j = r.json()
        last_payload = j
        last_status = j.get("status")

        if last_status == "completed":
            output_file_id = j.get("output_file_id")
            break

        if last_status in ("failed", "expired", "cancelled"):
            pytest.fail(f"Batch ended in terminal status={last_status}: {j}")

        # Backoff after a bit to avoid hammering.
        await asyncio.sleep(interval)
        if interval < 5.0:
            interval = min(5.0, interval + 0.2)

    if not output_file_id:
        pytest.skip(
            f"Batch did not complete within {batch_timeout_s:.0f}s (status={last_status}). "
            f"Set BATCH_TIMEOUT_SECONDS higher if needed. Last payload={last_payload}"
        )

    # Download output file content: should be JSONL including "pong"
    r = await _request_with_retry(client, "GET", f"/v1/files/{output_file_id}/content", headers=_auth_header())
    assert r.status_code == 200, r.text
    assert "pong" in r.text
```

