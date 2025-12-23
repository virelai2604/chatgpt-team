# ChatGPT Sync
Repo: chatgpt-team
Base: origin/main
Base commit (merge-base): 6c3184a03e0dfa370ba32732818685d823f35eb4
Dirs: app tests static schemas
Root files: project-tree.md pyproject.toml
Mode: changes
Generated: 2025-12-23T15:29:00+07:00

## CHANGE SUMMARY (since 6c3184a03e0dfa370ba32732818685d823f35eb4, includes worktree)

```
M	app/api/forward_openai.py
M	app/core/http_client.py
M	app/http_client.py
M	app/middleware/validation.py
M	app/routes/containers.py
```

## PATCH (since 6c3184a03e0dfa370ba32732818685d823f35eb4, includes worktree)

```diff
diff --git a/app/api/forward_openai.py b/app/api/forward_openai.py
index af35c54..e391f35 100755
--- a/app/api/forward_openai.py
+++ b/app/api/forward_openai.py
@@ -3,24 +3,27 @@ from __future__ import annotations
 import re
 from typing import Any, Dict, Mapping, Optional
 
-import httpx
 from fastapi import HTTPException, Request
 from fastapi.responses import Response, StreamingResponse
 
 from app.core.config import get_settings
-from app.http_client import get_async_httpx_client
-
+from app.core.http_client import get_async_httpx_client
 
 # --- Streaming route detection --------------------------------------------------------
 
-_SSE_PATH_RE = re.compile(r"^/v1/(responses|chat/completions)$")
+# Include :stream variants used by some OpenAI endpoints.
+_SSE_PATH_RE = re.compile(r"^/v1/(responses(?::stream)?|chat/completions(?::stream)?)$")
 
 
 def _is_sse_path(path: str) -> bool:
-    """Return True if an upstream route is expected to stream via SSE."""
     return _SSE_PATH_RE.match(path) is not None
 
 
+def _accepts_sse(headers: Mapping[str, str]) -> bool:
+    accept = headers.get("accept", "") or headers.get("Accept", "")
+    return "text/event-stream" in accept.lower()
+
+
 # --- Header/url helpers ---------------------------------------------------------------
 
 def _join_url(base: str, path: str) -> str:
@@ -28,7 +31,9 @@ def _join_url(base: str, path: str) -> str:
 
 
 def _filter_inbound_headers(headers: Mapping[str, str]) -> Dict[str, str]:
-    """Remove hop-by-hop and unsafe headers before proxying upstream."""
+    """
+    Remove hop-by-hop and unsafe headers before proxying upstream.
+    """
     out: Dict[str, str] = {}
     for k, v in headers.items():
         lk = k.lower()
@@ -49,7 +54,9 @@ def _filter_inbound_headers(headers: Mapping[str, str]) -> Dict[str, str]:
 
 
 def _filter_upstream_headers(headers: Mapping[str, str]) -> Dict[str, str]:
-    """Remove hop-by-hop/encoding headers from upstream response."""
+    """
+    Remove hop-by-hop/encoding headers from upstream response.
+    """
     out: Dict[str, str] = {}
     for k, v in headers.items():
         lk = k.lower()
@@ -64,21 +71,55 @@ def filter_upstream_headers(headers: Mapping[str, str]) -> Dict[str, str]:
     return _filter_upstream_headers(headers)
 
 
-def build_upstream_url(request: Request, base_url: str, *, path_override: Optional[str] = None) -> str:
-    """Build the upstream URL, preserving the original query string."""
-    path = path_override or request.url.path
-    url = _join_url(base_url, path)
-    if request.url.query:
-        url = f"{url}?{request.url.query}"
-    return url
-
-
-def _get_timeout_seconds(settings: Any) -> float:
-    """Back-compat: support multiple config field names."""
+def build_upstream_url(*args: Any, **kwargs: Any) -> str:
+    """
+    Backwards-compatible URL builder.
+
+    Supported call styles:
+      1) New style:
+           build_upstream_url(request, base_url, path_override="/v1/...")
+      2) Legacy style:
+           build_upstream_url("/v1/...", request=request, base_url="https://api.openai.com")
+           build_upstream_url("/v1/...")
+    """
+    # New style: (request, base_url, path_override=...)
+    if len(args) >= 2 and isinstance(args[0], Request) and isinstance(args[1], str):
+        request: Request = args[0]
+        base_url: str = args[1]
+        path_override: Optional[str] = kwargs.get("path_override")
+        path = path_override or request.url.path
+        url = _join_url(base_url, path)
+        if request.url.query:
+            url = f"{url}?{request.url.query}"
+        return url
+
+    # Legacy style: (path, ...)
+    if len(args) >= 1 and isinstance(args[0], str):
+        path: str = args[0]
+        request: Optional[Request] = kwargs.get("request")
+        base_url: Optional[str] = kwargs.get("base_url")
+
+        s = get_settings()
+        base = base_url or getattr(s, "openai_base_url", None) or "https://api.openai.com"
+
+        url = _join_url(base, path)
+        if request is not None and request.url.query:
+            url = f"{url}?{request.url.query}"
+        return url
+
+    raise TypeError("build_upstream_url() received unsupported arguments")
+
+
+def _get_timeout_seconds(settings: Optional[Any] = None) -> float:
+    """
+    Back-compat: support multiple config field names and legacy call sites that
+    invoke _get_timeout_seconds() with no args.
+    """
+    s = settings or get_settings()
     for name in ("proxy_timeout_seconds", "proxy_timeout", "proxy_timeout_s"):
-        if hasattr(settings, name):
+        if hasattr(s, name):
             try:
-                return float(getattr(settings, name))
+                return float(getattr(s, name))
             except Exception:
                 pass
     return 120.0
@@ -86,30 +127,35 @@ def _get_timeout_seconds(settings: Any) -> float:
 
 def build_outbound_headers(
     inbound_headers: Mapping[str, str],
-    openai_api_key: str,
+    openai_api_key: Optional[str] = None,
     content_type: Optional[str] = None,
     forward_accept: bool = True,
     path_hint: Optional[str] = None,
 ) -> Dict[str, str]:
     """
-    Create upstream request headers.
+    Build headers for upstream OpenAI request.
 
-    This function intentionally accepts legacy parameters (forward_accept, path_hint)
-    so older route modules can call it without raising TypeError.
+    - If `openai_api_key` is not provided, it is taken from settings.
+    - `path_hint` is accepted for older callers (not required for current behavior).
     """
-    # forward_accept/path_hint are retained for compatibility; current implementation
-    # always forwards the inbound Accept header if present.
-    _ = forward_accept
-    _ = path_hint
+    _ = path_hint  # retained for compatibility
+
+    s = get_settings()
+    api_key = openai_api_key or getattr(s, "openai_api_key", None)
+    if not api_key:
+        raise HTTPException(status_code=500, detail="Missing OPENAI_API_KEY")
 
     out = _filter_inbound_headers(inbound_headers)
-    out["Authorization"] = f"Bearer {openai_api_key}"
+
+    if not forward_accept:
+        out.pop("Accept", None)
+
+    out["Authorization"] = f"Bearer {api_key}"
 
     if content_type:
         out["Content-Type"] = content_type
 
-    # OpenAI-Beta header can contain multiple comma-separated flags.
-    s = get_settings()
+    # Optional OpenAI-Beta flags (safe to include; deduped).
     beta_values = []
     if getattr(s, "openai_assistants_beta", False):
         beta_values.append("assistants=v2")
@@ -144,7 +190,9 @@ async def forward_openai_request_to_path(
     method_override: Optional[str] = None,
     path_override: Optional[str] = None,
 ) -> Response:
-    """Forward the inbound FastAPI request to OpenAI, optionally overriding method/path."""
+    """
+    Forward an inbound FastAPI request to OpenAI, optionally overriding method/path.
+    """
     s = get_settings()
     base_url = getattr(s, "openai_base_url", None) or "https://api.openai.com"
     api_key = getattr(s, "openai_api_key", None)
@@ -155,21 +203,25 @@ async def forward_openai_request_to_path(
     upstream_url = build_upstream_url(request, base_url, path_override=path_override)
 
     body = await request.body()
+    inbound_ct = request.headers.get("content-type")
+
     headers = build_outbound_headers(
         request.headers,
-        api_key,
-        content_type=request.headers.get("content-type"),
+        openai_api_key=api_key,
+        content_type=inbound_ct,
+        forward_accept=True,
+        path_hint=path_override or request.url.path,
     )
 
     # If there is a body but the client omitted Content-Type, default to JSON.
-    if body and not any(k.lower() == "content-type" for k in headers.keys()):
+    if body and not inbound_ct:
         headers["Content-Type"] = "application/json"
 
     timeout_s = _get_timeout_seconds(s)
     client = get_async_httpx_client(timeout=timeout_s)
 
     effective_path = path_override or request.url.path
-    if _is_sse_path(effective_path):
+    if _accepts_sse(request.headers) or _is_sse_path(effective_path):
         async with client.stream(method, upstream_url, headers=headers, content=body) as upstream:
             return StreamingResponse(
                 upstream.aiter_bytes(),
@@ -188,7 +240,6 @@ async def forward_openai_request_to_path(
 
 
 async def forward_openai_request(request: Request) -> Response:
-    """Forward the request to the same upstream path."""
     return await forward_openai_request_to_path(request)
 
 
@@ -203,11 +254,9 @@ async def forward_openai_method_path(
     """
     Forward to a specific upstream method/path.
 
-    Supports two call styles:
-      - New style (keyword-only):
-          forward_openai_method_path(method=..., path=..., query=..., json_body=..., inbound_headers=...)
-      - Legacy style (positional):
-          forward_openai_method_path(<method>, <path>, <request>)
+    Supports:
+      - Legacy positional: forward_openai_method_path(<method>, <path>, <request>)
+      - New keyword-only: forward_openai_method_path(method=..., path=..., query=..., json_body=..., inbound_headers=...)
     """
     # Legacy style: (method, path, request)
     if (
@@ -238,11 +287,12 @@ async def forward_openai_method_path(
         raise HTTPException(status_code=500, detail="Missing OPENAI_API_KEY")
 
     url = _join_url(base_url, path)
-
     headers = build_outbound_headers(
         inbound_headers or {},
-        api_key,
+        openai_api_key=api_key,
         content_type="application/json",
+        forward_accept=True,
+        path_hint=path,
     )
 
     timeout_s = _get_timeout_seconds(s)
@@ -257,12 +307,38 @@ async def forward_openai_method_path(
     )
 
 
-async def forward_responses_create(request: Request, body: Any) -> Response:
-    """Convenience wrapper for POST /v1/responses using the proxy envelope body."""
-    return await forward_openai_method_path(
-        method="POST",
-        path="/v1/responses",
-        query=dict(request.query_params),
-        json_body=body,
-        inbound_headers=request.headers,
+async def forward_embeddings_create(body: Any) -> Dict[str, Any]:
+    """
+    Used by app.routes.embeddings. Returns the upstream JSON payload.
+    """
+    s = get_settings()
+    base_url = getattr(s, "openai_base_url", None) or "https://api.openai.com"
+    api_key = getattr(s, "openai_api_key", None)
+    if not api_key:
+        raise HTTPException(status_code=500, detail="Missing OPENAI_API_KEY")
+
+    url = _join_url(base_url, "/v1/embeddings")
+    headers = build_outbound_headers(
+        {},
+        openai_api_key=api_key,
+        content_type="application/json",
+        forward_accept=False,
+        path_hint="/v1/embeddings",
     )
+
+    timeout_s = _get_timeout_seconds(s)
+    client = get_async_httpx_client(timeout=timeout_s)
+
+    resp = await client.post(url, json=body, headers=headers)
+    try:
+        payload = resp.json()
+    except Exception:
+        raise HTTPException(status_code=resp.status_code, detail=resp.text)
+
+    if resp.status_code >= 400:
+        # Preserve upstream error structure.
+        raise HTTPException(status_code=resp.status_code, detail=payload)
+
+    if not isinstance(payload, dict):
+        raise HTTPException(status_code=502, detail="Upstream returned non-object JSON for embeddings")
+    return payload
diff --git a/app/core/http_client.py b/app/core/http_client.py
index ea6d37b..6bb0e16 100644
--- a/app/core/http_client.py
+++ b/app/core/http_client.py
@@ -1,173 +1,87 @@
 from __future__ import annotations
 
-"""
-Canonical HTTP/OpenAI client factory for the relay.
-
-Design goals:
-- One pooled httpx AsyncClient per (event loop, timeout) for upstream forwarding
-- One pooled OpenAI AsyncOpenAI per (event loop, timeout) for SDK-style calls
-- Safe cleanup for reload/shutdown
-
-IMPORTANT:
-Do not paste terminal tracebacks into this file. A single stray line like:
-    ModuleNotFoundError: ...
-will cause a SyntaxError and prevent Uvicorn from importing the app.
-"""
-
 import asyncio
-from typing import Dict, Optional, Tuple, cast
+from typing import Dict, Optional, Tuple
 
 import httpx
-from openai import AsyncOpenAI, DefaultAsyncHttpxClient
+from openai import AsyncOpenAI
 
-from app.core.config import settings
-from app.utils.logger import get_logger
+from app.core.config import get_settings
 
-log = get_logger(__name__)
+# Loop-local caches: each running event loop gets its own clients.
+_LOOP_CLIENTS: Dict[int, Tuple[AsyncOpenAI, httpx.AsyncClient]] = {}
 
-# Keyed by (id(loop), timeout_seconds)
-_HTTPX_CLIENTS: Dict[Tuple[int, float], httpx.AsyncClient] = {}
-_OPENAI_CLIENTS: Dict[Tuple[int, float], AsyncOpenAI] = {}
 
-_lock = asyncio.Lock()
+def _loop_id() -> int:
+    try:
+        loop = asyncio.get_running_loop()
+    except RuntimeError:
+        # No running loop; fall back to current loop (best effort).
+        loop = asyncio.get_event_loop()
+    return id(loop)
 
 
-def _get_setting(name_snake: str, name_upper: str, default=None):
+def get_async_openai_client(*, timeout: Optional[float] = None) -> AsyncOpenAI:
     """
-    Read a setting from either snake_case or UPPER_CASE attributes.
+    Return an AsyncOpenAI client that shares a loop-local httpx.AsyncClient.
+
+    Optional:
+      - timeout: override the httpx timeout (seconds) for this loop's shared client.
     """
-    if hasattr(settings, name_snake):
-        return getattr(settings, name_snake)
-    if hasattr(settings, name_upper):
-        return getattr(settings, name_upper)
-    return default
-
-
-def _default_timeout_seconds() -> float:
-    # Prefer PROXY timeout for relay->OpenAI forwarding.
-    v = _get_setting("proxy_timeout_seconds", "PROXY_TIMEOUT_SECONDS", None)
-    if v is None:
-        v = _get_setting("relay_timeout_seconds", "RELAY_TIMEOUT_SECONDS", 90)
-    try:
-        return float(v)
-    except Exception:
-        return 90.0
+    openai_client, _ = _get_or_create_clients(timeout=timeout)
+    return openai_client
 
 
-def _normalize_base_url_for_sdk(base_url: str) -> str:
+def get_async_httpx_client(*, timeout: Optional[float] = None) -> httpx.AsyncClient:
     """
-    The OpenAI SDK expects base_url ending with /v1 (it will append endpoint paths like /responses).
+    Return a loop-local shared httpx.AsyncClient.
+
+    Optional:
+      - timeout: override the client's timeout (seconds). If the client already exists,
+        we update its timeout best-effort.
     """
-    b = (base_url or "").strip()
-    if not b:
-        return "https://api.openai.com/v1"
-    b = b.rstrip("/")
-    if b.endswith("/v1"):
-        return b
-    return f"{b}/v1"
+    _, http_client = _get_or_create_clients(timeout=timeout)
+    if timeout is not None:
+        # Best-effort update; safe even if httpx internals change.
+        try:
+            http_client.timeout = httpx.Timeout(timeout)
+        except Exception:
+            pass
+    return http_client
 
 
-def _loop_id() -> int:
-    return id(asyncio.get_running_loop())
+def _get_or_create_clients(*, timeout: Optional[float]) -> Tuple[AsyncOpenAI, httpx.AsyncClient]:
+    lid = _loop_id()
+    if lid in _LOOP_CLIENTS:
+        return _LOOP_CLIENTS[lid]
 
+    settings = get_settings()
 
-async def get_async_httpx_client(timeout_s: Optional[float] = None) -> httpx.AsyncClient:
-    """
-    Shared httpx client for forwarding relay requests upstream.
-    """
-    t = float(timeout_s) if timeout_s is not None else _default_timeout_seconds()
-    key = (_loop_id(), t)
+    timeout_s = float(timeout) if timeout is not None else float(getattr(settings, "relay_timeout_seconds", 120.0))
+    http_client = httpx.AsyncClient(timeout=httpx.Timeout(timeout_s))
 
-    async with _lock:
-        client = _HTTPX_CLIENTS.get(key)
-        if client is not None:
-            return client
+    openai_client = AsyncOpenAI(
+        api_key=settings.openai_api_key,
+        base_url=getattr(settings, "openai_base_url", None) or "https://api.openai.com/v1",
+        http_client=http_client,
+    )
 
-        timeout = httpx.Timeout(t)
-        client = httpx.AsyncClient(timeout=timeout)
-        _HTTPX_CLIENTS[key] = client
-        return client
-
-
-async def get_async_openai_client(timeout_s: Optional[float] = None) -> AsyncOpenAI:
-    """
-    Shared OpenAI SDK client (AsyncOpenAI). Uses its own DefaultAsyncHttpxClient.
-    """
-    t = float(timeout_s) if timeout_s is not None else _default_timeout_seconds()
-    key = (_loop_id(), t)
-
-    async with _lock:
-        client = _OPENAI_CLIENTS.get(key)
-        if client is not None:
-            return client
-
-        api_key = cast(
-            str,
-            _get_setting("openai_api_key", "OPENAI_API_KEY", None),
-        )
-        api_base = cast(
-            str,
-            _get_setting("openai_api_base", "OPENAI_API_BASE", "https://api.openai.com/v1"),
-        )
-        organization = _get_setting("openai_organization", "OPENAI_ORGANIZATION", None)
-
-        # Optional: combine beta headers if present
-        assistants_beta = _get_setting("openai_assistants_beta", "OPENAI_ASSISTANTS_BETA", None)
-        realtime_beta = _get_setting("openai_realtime_beta", "OPENAI_REALTIME_BETA", None)
-        betas = [b for b in [assistants_beta, realtime_beta] if b]
-        default_headers = {}
-        if betas:
-            default_headers["OpenAI-Beta"] = ",".join(betas)
-
-        http_client = DefaultAsyncHttpxClient(timeout=httpx.Timeout(t))
-
-        client = AsyncOpenAI(
-            api_key=api_key,
-            base_url=_normalize_base_url_for_sdk(api_base),
-            organization=organization,
-            default_headers=default_headers or None,
-            http_client=http_client,
-        )
-        _OPENAI_CLIENTS[key] = client
-        return client
+    _LOOP_CLIENTS[lid] = (openai_client, http_client)
+    return openai_client, http_client
 
 
 async def close_async_clients() -> None:
     """
-    Close and clear all cached clients for the current process.
-    Useful on shutdown and reload.
+    Close all loop-local clients (safe to call at shutdown).
     """
-    async with _lock:
-        openai_items = list(_OPENAI_CLIENTS.items())
-        httpx_items = list(_HTTPX_CLIENTS.items())
-        _OPENAI_CLIENTS.clear()
-        _HTTPX_CLIENTS.clear()
-
-    # Close OpenAI clients (their internal http_client) first.
-    for (loop_id, timeout_s), client in openai_items:
-        try:
-            await client.close()
-        except Exception:
-            log.exception("Failed closing OpenAI client loop=%s timeout=%s", loop_id, timeout_s)
-
-    # Close httpx clients used for forwarding.
-    for (loop_id, timeout_s), client in httpx_items:
+    for lid, (openai_client, http_client) in list(_LOOP_CLIENTS.items()):
         try:
-            await client.aclose()
-        except Exception:
-            log.exception("Failed closing httpx client loop=%s timeout=%s", loop_id, timeout_s)
+            # OpenAI client uses the same http client; closing httpx is sufficient.
+            await http_client.aclose()
+        finally:
+            _LOOP_CLIENTS.pop(lid, None)
 
 
 async def aclose_all_clients() -> None:
-    """
-    Backwards-compatible alias.
-    """
+    # Back-compat alias
     await close_async_clients()
-
-
-__all__ = [
-    "get_async_httpx_client",
-    "get_async_openai_client",
-    "close_async_clients",
-    "aclose_all_clients",
-]
diff --git a/app/http_client.py b/app/http_client.py
index 97703ad..4071691 100644
--- a/app/http_client.py
+++ b/app/http_client.py
@@ -1,13 +1,14 @@
-from __future__ import annotations
-
-"""Compatibility shim.
+"""
+Compatibility shim for legacy imports.
 
-Historically some modules imported HTTP/OpenAI clients from `app.http_client`.
-The canonical implementation lives in `app.core.http_client`.
+Some modules historically imported client helpers from `app.http_client`.
+The canonical implementations live in `app.core.http_client`.
 
-This module re-exports the public helpers to avoid churn.
+This module re-exports the public helpers to avoid churn and circular edits.
 """
 
+from __future__ import annotations
+
 from app.core.http_client import (  # noqa: F401
     aclose_all_clients,
     close_async_clients,
diff --git a/app/middleware/validation.py b/app/middleware/validation.py
index 31b8916..5e6bdb8 100755
--- a/app/middleware/validation.py
+++ b/app/middleware/validation.py
@@ -1,78 +1,67 @@
 from __future__ import annotations
 
-from typing import Callable, Iterable, Set
-
 from starlette.middleware.base import BaseHTTPMiddleware
 from starlette.requests import Request
-from starlette.responses import JSONResponse, Response
+from starlette.responses import Response
+from starlette.status import HTTP_415_UNSUPPORTED_MEDIA_TYPE
 
+from app.core.logging import get_logger
+from app.models.error import ErrorResponse
 
-def _base_content_type(content_type_header: str) -> str:
-    # e.g. "application/json; charset=utf-8" -> "application/json"
-    return (content_type_header or "").split(";", 1)[0].strip().lower()
+logger = get_logger(__name__)
 
+_JSON_CT_PREFIX = "application/json"
+_MULTIPART_CT_PREFIX = "multipart/form-data"
 
-def _is_allowed_content_type(base_ct: str, allowed: Set[str]) -> bool:
-    if not base_ct:
-        return False
-    if base_ct in allowed:
-        return True
-    # Allow any vendor JSON: application/*+json
-    if base_ct.endswith("+json"):
-        return True
-    # Allow multipart with boundary parameter already stripped
-    if base_ct == "multipart/form-data":
+
+def _has_body(request: Request) -> bool:
+    """
+    Determine if the request is expected to have a body without consuming it.
+
+    - If Content-Length is present and > 0 => has body
+    - If Transfer-Encoding is present => has body
+    - Otherwise => assume no body
+    """
+    cl = request.headers.get("content-length")
+    if cl is not None:
+        try:
+            return int(cl) > 0
+        except ValueError:
+            # If Content-Length is malformed, be conservative.
+            return True
+
+    # Chunked uploads, etc.
+    if request.headers.get("transfer-encoding"):
         return True
+
     return False
 
 
 class ValidationMiddleware(BaseHTTPMiddleware):
     """
-    Enforce Content-Type for body-bearing methods, while allowing empty-body POSTs.
+    Reject unsupported content-types for methods that typically carry bodies.
 
-    Why:
-      - Some OpenAI endpoints (notably `/v1/uploads/{upload_id}/cancel`) accept POST with no body.
-      - Clients often omit Content-Type when body is empty.
-      - We still want strict enforcement when a body *is present*.
+    IMPORTANT: allow empty-body requests (e.g., POST cancel endpoints) even if
+    Content-Type is missing. Many clients send `Content-Length: 0` and no CT.
     """
 
-    def __init__(
-        self,
-        app,
-        *,
-        allowed_content_types: Iterable[str] | None = None,
-    ) -> None:
-        super().__init__(app)
-        self.allowed_content_types: Set[str] = set(
-            ct.strip().lower()
-            for ct in (allowed_content_types or ("application/json",))
-            if ct and ct.strip()
-        )
-        # Always allow multipart uploads (e.g. /v1/files, /v1/uploads/*/parts)
-        self.allowed_content_types.add("multipart/form-data")
-
-    async def dispatch(self, request: Request, call_next: Callable) -> Response:
-        method = request.method.upper()
-
-        # Only validate methods that commonly carry a body.
-        if method in {"POST", "PUT", "PATCH"}:
-            raw_ct = request.headers.get("content-type") or ""
-            base_ct = _base_content_type(raw_ct)
-
-            if not base_ct:
-                # No Content-Type provided. Allow only if the body is empty.
-                body = await request.body()  # Starlette caches this (safe for downstream).
-                if body:
-                    return JSONResponse(
-                        status_code=415,
-                        content={"detail": "Unsupported Media Type: ''"},
+    async def dispatch(self, request: Request, call_next) -> Response:
+        if request.method.upper() in {"POST", "PUT", "PATCH"}:
+            if _has_body(request):
+                content_type = request.headers.get("content-type", "")
+                if not (
+                    content_type.startswith(_JSON_CT_PREFIX)
+                    or content_type.startswith(_MULTIPART_CT_PREFIX)
+                ):
+                    logger.info(
+                        "ValidationMiddleware rejected request: method=%s path=%s content-type=%r",
+                        request.method,
+                        request.url.path,
+                        content_type,
                     )
-                return await call_next(request)
-
-            if not _is_allowed_content_type(base_ct, self.allowed_content_types):
-                return JSONResponse(
-                    status_code=415,
-                    content={"detail": f"Unsupported Media Type: '{base_ct}'"},
-                )
+                    err = ErrorResponse(
+                        detail=f"Unsupported Media Type: '{content_type}'",
+                    )
+                    return err.to_response(status_code=HTTP_415_UNSUPPORTED_MEDIA_TYPE)
 
         return await call_next(request)
diff --git a/app/routes/containers.py b/app/routes/containers.py
index 2ff4c40..8d4c690 100644
--- a/app/routes/containers.py
+++ b/app/routes/containers.py
@@ -1,11 +1,7 @@
 from __future__ import annotations
 
-from typing import Optional
-
-import httpx
-from fastapi import APIRouter, HTTPException, Request, Response
-from fastapi.responses import StreamingResponse
-from starlette.background import BackgroundTask
+from fastapi import APIRouter, Request
+from fastapi.responses import Response, StreamingResponse
 
 from app.api.forward_openai import (
     _get_timeout_seconds,
@@ -14,86 +10,48 @@ from app.api.forward_openai import (
     filter_upstream_headers,
     forward_openai_request,
 )
+from app.core.config import get_settings
 from app.core.http_client import get_async_httpx_client
-from app.utils.logger import relay_log as logger
 
 router = APIRouter(prefix="/v1", tags=["containers"])
 
 
-async def _forward(request: Request) -> Response:
-    logger.info("→ [containers] %s %s", request.method, request.url.path)
-    return await forward_openai_request(request)
-
-
-# ---- /v1/containers ----
 @router.get("/containers")
-async def containers_root_get(request: Request) -> Response:
-    return await _forward(request)
+async def containers_list(request: Request) -> Response:
+    return await forward_openai_request(request)
 
 
 @router.post("/containers")
-async def containers_root_post(request: Request) -> Response:
-    return await _forward(request)
+async def containers_create(request: Request) -> Response:
+    return await forward_openai_request(request)
 
 
 @router.head("/containers", include_in_schema=False)
-async def containers_root_head(request: Request) -> Response:
-    return await _forward(request)
+async def containers_head(request: Request) -> Response:
+    return await forward_openai_request(request)
 
 
 @router.options("/containers", include_in_schema=False)
-async def containers_root_options(request: Request) -> Response:
-    return await _forward(request)
+async def containers_options(request: Request) -> Response:
+    return await forward_openai_request(request)
 
 
-async def _container_file_content_head(container_id: str, file_id: str, request: Request) -> Response:
+@router.get("/containers/{container_id}/files/{file_id}/content")
+async def containers_file_content(request: Request, container_id: str, file_id: str) -> Response:
+    """
+    Stream container file content.
+
+    Critical behavior:
+      - Do NOT raise on upstream non-2xx.
+      - If upstream returns 4xx/5xx, read the body and return it with upstream status
+        (avoids relay 500 masking upstream errors).
+    """
     upstream_path = f"/v1/containers/{container_id}/files/{file_id}/content"
-    upstream_url = build_upstream_url(upstream_path)
-
-    headers = build_outbound_headers(
-        inbound_headers=request.headers,
-        content_type=None,
-        forward_accept=True,
-        path_hint=upstream_path,
-    )
-
-    # Forward Range if provided; otherwise minimal range for headers
-    range_hdr: Optional[str] = request.headers.get("range")
-    if range_hdr:
-        headers["Range"] = range_hdr
-    else:
-        headers["Range"] = "bytes=0-0"
-
-    client = get_async_httpx_client()
-    timeout = _get_timeout_seconds()
-
-    upstream_req = client.build_request(
-        method="GET",
-        url=upstream_url,
-        params=request.query_params,
-        headers=headers,
-    )
 
-    try:
-        upstream_resp = await client.send(upstream_req, stream=True, timeout=timeout, follow_redirects=True)
-    except httpx.TimeoutException as exc:
-        raise HTTPException(status_code=504, detail=f"Upstream timeout: {type(exc).__name__}") from exc
-    except httpx.RequestError as exc:
-        raise HTTPException(status_code=502, detail=f"Upstream request failed: {type(exc).__name__}") from exc
+    s = get_settings()
+    base_url = getattr(s, "openai_base_url", None) or "https://api.openai.com"
 
-    await upstream_resp.aclose()
-
-    return Response(
-        content=b"",
-        status_code=upstream_resp.status_code,
-        headers=filter_upstream_headers(upstream_resp.headers),
-        media_type=upstream_resp.headers.get("content-type"),
-    )
-
-
-async def _container_file_content_get(container_id: str, file_id: str, request: Request) -> Response:
-    upstream_path = f"/v1/containers/{container_id}/files/{file_id}/content"
-    upstream_url = build_upstream_url(upstream_path)
+    upstream_url = build_upstream_url(upstream_path, request=request, base_url=base_url)
 
     headers = build_outbound_headers(
         inbound_headers=request.headers,
@@ -102,62 +60,31 @@ async def _container_file_content_get(container_id: str, file_id: str, request:
         path_hint=upstream_path,
     )
 
-    # Forward Range if provided (best-effort)
-    range_hdr: Optional[str] = request.headers.get("range")
-    if range_hdr:
-        headers["Range"] = range_hdr
-
-    client = get_async_httpx_client()
-    timeout = _get_timeout_seconds()
-
-    upstream_req = client.build_request(
-        method="GET",
-        url=upstream_url,
-        params=request.query_params,
-        headers=headers,
-    )
-
-    try:
-        upstream_resp = await client.send(upstream_req, stream=True, timeout=timeout, follow_redirects=True)
-    except httpx.TimeoutException as exc:
-        raise HTTPException(status_code=504, detail=f"Upstream timeout: {type(exc).__name__}") from exc
-    except httpx.RequestError as exc:
-        raise HTTPException(status_code=502, detail=f"Upstream request failed: {type(exc).__name__}") from exc
-
-    if upstream_resp.status_code >= 400:
-        error_body = await upstream_resp.aread()
-        await upstream_resp.aclose()
-        return Response(
-            content=error_body,
-            status_code=upstream_resp.status_code,
-            headers=filter_upstream_headers(upstream_resp.headers),
-            media_type=upstream_resp.headers.get("content-type"),
+    timeout_s = _get_timeout_seconds(s)
+    client = get_async_httpx_client(timeout=timeout_s)
+
+    async with client.stream("GET", upstream_url, headers=headers) as upstream:
+        status = upstream.status_code
+        resp_headers = filter_upstream_headers(upstream.headers)
+        media_type = upstream.headers.get("content-type")
+
+        if status >= 400:
+            content = await upstream.aread()
+            return Response(
+                content=content,
+                status_code=status,
+                headers=resp_headers,
+                media_type=media_type,
+            )
+
+        return StreamingResponse(
+            upstream.aiter_bytes(),
+            status_code=status,
+            headers=resp_headers,
+            media_type=media_type,
         )
 
-    return StreamingResponse(
-        upstream_resp.aiter_bytes(),
-        status_code=upstream_resp.status_code,
-        headers=filter_upstream_headers(upstream_resp.headers),
-        media_type=upstream_resp.headers.get("content-type"),
-        background=BackgroundTask(upstream_resp.aclose),
-    )
-
-
-@router.get("/containers/{container_id}/files/{file_id}/content")
-async def container_file_content_get(container_id: str, file_id: str, request: Request) -> Response:
-    return await _container_file_content_get(container_id=container_id, file_id=file_id, request=request)
 
-
-@router.head("/containers/{container_id}/files/{file_id}/content")
-async def container_file_content_head(container_id: str, file_id: str, request: Request) -> Response:
-    return await _container_file_content_head(container_id=container_id, file_id=file_id, request=request)
-
-
-@router.api_route(
-    "/containers/{path:path}",
-    methods=["GET", "POST", "DELETE", "HEAD", "OPTIONS"],
-    include_in_schema=False,
-)
-async def containers_subpaths(path: str, request: Request) -> Response:
-    logger.info("→ [containers/*] %s %s", request.method, request.url.path)
+@router.head("/containers/{container_id}/files/{file_id}/content", include_in_schema=False)
+async def containers_file_content_head(request: Request, container_id: str, file_id: str) -> Response:
     return await forward_openai_request(request)
```

## CURRENT CONTENT OF CHANGED FILES (WORKTREE)

## FILE: app/api/forward_openai.py @ WORKTREE
```
from __future__ import annotations

import re
from typing import Any, Dict, Mapping, Optional

from fastapi import HTTPException, Request
from fastapi.responses import Response, StreamingResponse

from app.core.config import get_settings
from app.core.http_client import get_async_httpx_client

# --- Streaming route detection --------------------------------------------------------

# Include :stream variants used by some OpenAI endpoints.
_SSE_PATH_RE = re.compile(r"^/v1/(responses(?::stream)?|chat/completions(?::stream)?)$")


def _is_sse_path(path: str) -> bool:
    return _SSE_PATH_RE.match(path) is not None


def _accepts_sse(headers: Mapping[str, str]) -> bool:
    accept = headers.get("accept", "") or headers.get("Accept", "")
    return "text/event-stream" in accept.lower()


# --- Header/url helpers ---------------------------------------------------------------

def _join_url(base: str, path: str) -> str:
    return f"{base.rstrip('/')}/{path.lstrip('/')}"


def _filter_inbound_headers(headers: Mapping[str, str]) -> Dict[str, str]:
    """
    Remove hop-by-hop and unsafe headers before proxying upstream.
    """
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
    """
    Remove hop-by-hop/encoding headers from upstream response.
    """
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


def build_upstream_url(*args: Any, **kwargs: Any) -> str:
    """
    Backwards-compatible URL builder.

    Supported call styles:
      1) New style:
           build_upstream_url(request, base_url, path_override="/v1/...")
      2) Legacy style:
           build_upstream_url("/v1/...", request=request, base_url="https://api.openai.com")
           build_upstream_url("/v1/...")
    """
    # New style: (request, base_url, path_override=...)
    if len(args) >= 2 and isinstance(args[0], Request) and isinstance(args[1], str):
        request: Request = args[0]
        base_url: str = args[1]
        path_override: Optional[str] = kwargs.get("path_override")
        path = path_override or request.url.path
        url = _join_url(base_url, path)
        if request.url.query:
            url = f"{url}?{request.url.query}"
        return url

    # Legacy style: (path, ...)
    if len(args) >= 1 and isinstance(args[0], str):
        path: str = args[0]
        request: Optional[Request] = kwargs.get("request")
        base_url: Optional[str] = kwargs.get("base_url")

        s = get_settings()
        base = base_url or getattr(s, "openai_base_url", None) or "https://api.openai.com"

        url = _join_url(base, path)
        if request is not None and request.url.query:
            url = f"{url}?{request.url.query}"
        return url

    raise TypeError("build_upstream_url() received unsupported arguments")


def _get_timeout_seconds(settings: Optional[Any] = None) -> float:
    """
    Back-compat: support multiple config field names and legacy call sites that
    invoke _get_timeout_seconds() with no args.
    """
    s = settings or get_settings()
    for name in ("proxy_timeout_seconds", "proxy_timeout", "proxy_timeout_s"):
        if hasattr(s, name):
            try:
                return float(getattr(s, name))
            except Exception:
                pass
    return 120.0


def build_outbound_headers(
    inbound_headers: Mapping[str, str],
    openai_api_key: Optional[str] = None,
    content_type: Optional[str] = None,
    forward_accept: bool = True,
    path_hint: Optional[str] = None,
) -> Dict[str, str]:
    """
    Build headers for upstream OpenAI request.

    - If `openai_api_key` is not provided, it is taken from settings.
    - `path_hint` is accepted for older callers (not required for current behavior).
    """
    _ = path_hint  # retained for compatibility

    s = get_settings()
    api_key = openai_api_key or getattr(s, "openai_api_key", None)
    if not api_key:
        raise HTTPException(status_code=500, detail="Missing OPENAI_API_KEY")

    out = _filter_inbound_headers(inbound_headers)

    if not forward_accept:
        out.pop("Accept", None)

    out["Authorization"] = f"Bearer {api_key}"

    if content_type:
        out["Content-Type"] = content_type

    # Optional OpenAI-Beta flags (safe to include; deduped).
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
    """
    Forward an inbound FastAPI request to OpenAI, optionally overriding method/path.
    """
    s = get_settings()
    base_url = getattr(s, "openai_base_url", None) or "https://api.openai.com"
    api_key = getattr(s, "openai_api_key", None)
    if not api_key:
        raise HTTPException(status_code=500, detail="Missing OPENAI_API_KEY")

    method = (method_override or request.method).upper()
    upstream_url = build_upstream_url(request, base_url, path_override=path_override)

    body = await request.body()
    inbound_ct = request.headers.get("content-type")

    headers = build_outbound_headers(
        request.headers,
        openai_api_key=api_key,
        content_type=inbound_ct,
        forward_accept=True,
        path_hint=path_override or request.url.path,
    )

    # If there is a body but the client omitted Content-Type, default to JSON.
    if body and not inbound_ct:
        headers["Content-Type"] = "application/json"

    timeout_s = _get_timeout_seconds(s)
    client = get_async_httpx_client(timeout=timeout_s)

    effective_path = path_override or request.url.path
    if _accepts_sse(request.headers) or _is_sse_path(effective_path):
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

    Supports:
      - Legacy positional: forward_openai_method_path(<method>, <path>, <request>)
      - New keyword-only: forward_openai_method_path(method=..., path=..., query=..., json_body=..., inbound_headers=...)
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
        openai_api_key=api_key,
        content_type="application/json",
        forward_accept=True,
        path_hint=path,
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


async def forward_embeddings_create(body: Any) -> Dict[str, Any]:
    """
    Used by app.routes.embeddings. Returns the upstream JSON payload.
    """
    s = get_settings()
    base_url = getattr(s, "openai_base_url", None) or "https://api.openai.com"
    api_key = getattr(s, "openai_api_key", None)
    if not api_key:
        raise HTTPException(status_code=500, detail="Missing OPENAI_API_KEY")

    url = _join_url(base_url, "/v1/embeddings")
    headers = build_outbound_headers(
        {},
        openai_api_key=api_key,
        content_type="application/json",
        forward_accept=False,
        path_hint="/v1/embeddings",
    )

    timeout_s = _get_timeout_seconds(s)
    client = get_async_httpx_client(timeout=timeout_s)

    resp = await client.post(url, json=body, headers=headers)
    try:
        payload = resp.json()
    except Exception:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)

    if resp.status_code >= 400:
        # Preserve upstream error structure.
        raise HTTPException(status_code=resp.status_code, detail=payload)

    if not isinstance(payload, dict):
        raise HTTPException(status_code=502, detail="Upstream returned non-object JSON for embeddings")
    return payload
```

## FILE: app/core/http_client.py @ WORKTREE
```
from __future__ import annotations

import asyncio
from typing import Dict, Optional, Tuple

import httpx
from openai import AsyncOpenAI

from app.core.config import get_settings

# Loop-local caches: each running event loop gets its own clients.
_LOOP_CLIENTS: Dict[int, Tuple[AsyncOpenAI, httpx.AsyncClient]] = {}


def _loop_id() -> int:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # No running loop; fall back to current loop (best effort).
        loop = asyncio.get_event_loop()
    return id(loop)


def get_async_openai_client(*, timeout: Optional[float] = None) -> AsyncOpenAI:
    """
    Return an AsyncOpenAI client that shares a loop-local httpx.AsyncClient.

    Optional:
      - timeout: override the httpx timeout (seconds) for this loop's shared client.
    """
    openai_client, _ = _get_or_create_clients(timeout=timeout)
    return openai_client


def get_async_httpx_client(*, timeout: Optional[float] = None) -> httpx.AsyncClient:
    """
    Return a loop-local shared httpx.AsyncClient.

    Optional:
      - timeout: override the client's timeout (seconds). If the client already exists,
        we update its timeout best-effort.
    """
    _, http_client = _get_or_create_clients(timeout=timeout)
    if timeout is not None:
        # Best-effort update; safe even if httpx internals change.
        try:
            http_client.timeout = httpx.Timeout(timeout)
        except Exception:
            pass
    return http_client


def _get_or_create_clients(*, timeout: Optional[float]) -> Tuple[AsyncOpenAI, httpx.AsyncClient]:
    lid = _loop_id()
    if lid in _LOOP_CLIENTS:
        return _LOOP_CLIENTS[lid]

    settings = get_settings()

    timeout_s = float(timeout) if timeout is not None else float(getattr(settings, "relay_timeout_seconds", 120.0))
    http_client = httpx.AsyncClient(timeout=httpx.Timeout(timeout_s))

    openai_client = AsyncOpenAI(
        api_key=settings.openai_api_key,
        base_url=getattr(settings, "openai_base_url", None) or "https://api.openai.com/v1",
        http_client=http_client,
    )

    _LOOP_CLIENTS[lid] = (openai_client, http_client)
    return openai_client, http_client


async def close_async_clients() -> None:
    """
    Close all loop-local clients (safe to call at shutdown).
    """
    for lid, (openai_client, http_client) in list(_LOOP_CLIENTS.items()):
        try:
            # OpenAI client uses the same http client; closing httpx is sufficient.
            await http_client.aclose()
        finally:
            _LOOP_CLIENTS.pop(lid, None)


async def aclose_all_clients() -> None:
    # Back-compat alias
    await close_async_clients()
```

## FILE: app/http_client.py @ WORKTREE
```
"""
Compatibility shim for legacy imports.

Some modules historically imported client helpers from `app.http_client`.
The canonical implementations live in `app.core.http_client`.

This module re-exports the public helpers to avoid churn and circular edits.
"""

from __future__ import annotations

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
```

## FILE: app/middleware/validation.py @ WORKTREE
```
from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.status import HTTP_415_UNSUPPORTED_MEDIA_TYPE

from app.core.logging import get_logger
from app.models.error import ErrorResponse

logger = get_logger(__name__)

_JSON_CT_PREFIX = "application/json"
_MULTIPART_CT_PREFIX = "multipart/form-data"


def _has_body(request: Request) -> bool:
    """
    Determine if the request is expected to have a body without consuming it.

    - If Content-Length is present and > 0 => has body
    - If Transfer-Encoding is present => has body
    - Otherwise => assume no body
    """
    cl = request.headers.get("content-length")
    if cl is not None:
        try:
            return int(cl) > 0
        except ValueError:
            # If Content-Length is malformed, be conservative.
            return True

    # Chunked uploads, etc.
    if request.headers.get("transfer-encoding"):
        return True

    return False


class ValidationMiddleware(BaseHTTPMiddleware):
    """
    Reject unsupported content-types for methods that typically carry bodies.

    IMPORTANT: allow empty-body requests (e.g., POST cancel endpoints) even if
    Content-Type is missing. Many clients send `Content-Length: 0` and no CT.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.method.upper() in {"POST", "PUT", "PATCH"}:
            if _has_body(request):
                content_type = request.headers.get("content-type", "")
                if not (
                    content_type.startswith(_JSON_CT_PREFIX)
                    or content_type.startswith(_MULTIPART_CT_PREFIX)
                ):
                    logger.info(
                        "ValidationMiddleware rejected request: method=%s path=%s content-type=%r",
                        request.method,
                        request.url.path,
                        content_type,
                    )
                    err = ErrorResponse(
                        detail=f"Unsupported Media Type: '{content_type}'",
                    )
                    return err.to_response(status_code=HTTP_415_UNSUPPORTED_MEDIA_TYPE)

        return await call_next(request)
```

## FILE: app/routes/containers.py @ WORKTREE
```
from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import Response, StreamingResponse

from app.api.forward_openai import (
    _get_timeout_seconds,
    build_outbound_headers,
    build_upstream_url,
    filter_upstream_headers,
    forward_openai_request,
)
from app.core.config import get_settings
from app.core.http_client import get_async_httpx_client

router = APIRouter(prefix="/v1", tags=["containers"])


@router.get("/containers")
async def containers_list(request: Request) -> Response:
    return await forward_openai_request(request)


@router.post("/containers")
async def containers_create(request: Request) -> Response:
    return await forward_openai_request(request)


@router.head("/containers", include_in_schema=False)
async def containers_head(request: Request) -> Response:
    return await forward_openai_request(request)


@router.options("/containers", include_in_schema=False)
async def containers_options(request: Request) -> Response:
    return await forward_openai_request(request)


@router.get("/containers/{container_id}/files/{file_id}/content")
async def containers_file_content(request: Request, container_id: str, file_id: str) -> Response:
    """
    Stream container file content.

    Critical behavior:
      - Do NOT raise on upstream non-2xx.
      - If upstream returns 4xx/5xx, read the body and return it with upstream status
        (avoids relay 500 masking upstream errors).
    """
    upstream_path = f"/v1/containers/{container_id}/files/{file_id}/content"

    s = get_settings()
    base_url = getattr(s, "openai_base_url", None) or "https://api.openai.com"

    upstream_url = build_upstream_url(upstream_path, request=request, base_url=base_url)

    headers = build_outbound_headers(
        inbound_headers=request.headers,
        content_type=None,
        forward_accept=True,
        path_hint=upstream_path,
    )

    timeout_s = _get_timeout_seconds(s)
    client = get_async_httpx_client(timeout=timeout_s)

    async with client.stream("GET", upstream_url, headers=headers) as upstream:
        status = upstream.status_code
        resp_headers = filter_upstream_headers(upstream.headers)
        media_type = upstream.headers.get("content-type")

        if status >= 400:
            content = await upstream.aread()
            return Response(
                content=content,
                status_code=status,
                headers=resp_headers,
                media_type=media_type,
            )

        return StreamingResponse(
            upstream.aiter_bytes(),
            status_code=status,
            headers=resp_headers,
            media_type=media_type,
        )


@router.head("/containers/{container_id}/files/{file_id}/content", include_in_schema=False)
async def containers_file_content_head(request: Request, container_id: str, file_id: str) -> Response:
    return await forward_openai_request(request)
```

