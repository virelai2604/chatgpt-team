# ChatGPT Sync
Repo: chatgpt-team
Base: origin/main
Base commit (merge-base): bf2827ffaae201a2b88fa5e76d49cf63d1db1848
Dirs: app tests static schemas
Root files: project-tree.md pyproject.toml
Mode: changes
Generated: 2025-12-22T18:23:38+07:00

## CHANGE SUMMARY (since bf2827ffaae201a2b88fa5e76d49cf63d1db1848, includes worktree)

```
M	app/api/forward_openai.py
M	project-tree.md
```

## PATCH (since bf2827ffaae201a2b88fa5e76d49cf63d1db1848, includes worktree)

```diff
diff --git a/app/api/forward_openai.py b/app/api/forward_openai.py
index 9fca317..275aab4 100755
--- a/app/api/forward_openai.py
+++ b/app/api/forward_openai.py
@@ -15,14 +15,24 @@ from app.utils.logger import relay_log
 try:
     from app.core.config import get_settings  # type: ignore
 except ImportError:  # pragma: no cover
-    from app.core.config import settings as _settings  # type: ignore
+    get_settings = None  # type: ignore
 
-    def get_settings():
-        return _settings
+try:
+    from app.core.config import settings as module_settings  # type: ignore
+except ImportError:  # pragma: no cover
+    module_settings = None  # type: ignore
+
+
+def _settings() -> Any:
+    if get_settings is not None:
+        return get_settings()
+    if module_settings is not None:
+        return module_settings
+    raise RuntimeError("Settings not available (expected get_settings() or settings)")
 
 
 # -------------------------
-# URL + header normalization
+# Header / URL helpers
 # -------------------------
 
 _HOP_BY_HOP_HEADERS = {
@@ -38,280 +48,237 @@ _HOP_BY_HOP_HEADERS = {
 
 
 def normalize_base_url(base_url: str) -> str:
-    """Normalize base to scheme://host[:port] (no trailing /, no /v1)."""
-    base = (base_url or "").strip()
-    if not base:
-        return "https://api.openai.com"
-    base = base.rstrip("/")
-    if base.endswith("/v1"):
-        base = base[: -len("/v1")]
-    return base.rstrip("/")
-
-
-def normalize_upstream_path(path: str) -> str:
-    """Ensure path starts with /v1."""
+    """
+    Normalize an OpenAI base URL for consistent join semantics.
+    Accepts:
+      - https://api.openai.com
+      - https://api.openai.com/v1
+    Returns a base ending with /v1
+    """
+    b = (base_url or "").strip()
+    if not b:
+        raise ValueError("OPENAI_API_BASE is empty")
+    b = b.rstrip("/")
+    if b.endswith("/v1"):
+        return b
+    return b + "/v1"
+
+
+def join_url(base_v1: str, path: str) -> str:
+    base_v1 = normalize_base_url(base_v1)
     p = (path or "").strip()
     if not p.startswith("/"):
         p = "/" + p
-    if not p.startswith("/v1/") and p != "/v1":
-        # allow callers to pass "/responses" or "/v1/responses"
-        if p.startswith("/"):
-            p = "/v1" + p
-        else:
-            p = "/v1/" + p
-    return p
+    # If path already includes /v1, strip it so we don't double it.
+    if p.startswith("/v1/"):
+        p = p[3:]
+    elif p == "/v1":
+        p = ""
+    return base_v1 + p
 
 
-def build_upstream_url(path: str) -> str:
-    settings = get_settings()
-    base = normalize_base_url(getattr(settings, "openai_base_url", "https://api.openai.com"))
-    p = normalize_upstream_path(path)
-    return f"{base}{p}"
-
-
-def filter_upstream_headers(headers: Mapping[str, str]) -> dict[str, str]:
-    """Strip hop-by-hop headers and anything that shouldn't be forwarded back to the client."""
+def _filter_inbound_headers(headers: Mapping[str, str]) -> dict[str, str]:
     out: dict[str, str] = {}
     for k, v in headers.items():
         lk = k.lower()
         if lk in _HOP_BY_HOP_HEADERS:
             continue
-        # Let FastAPI/Uvicorn manage content-length/transfer-encoding.
-        if lk in {"content-length", "transfer-encoding"}:
+        # Never forward the relay's own Authorization header upstream.
+        if lk == "authorization":
             continue
         out[k] = v
     return out
 
 
 def build_outbound_headers(
-    inbound_headers: Optional[Mapping[str, str]] = None,
     *,
-    content_type: Optional[str] = None,
-    accept: Optional[str] = None,
+    inbound_headers: Mapping[str, str],
+    openai_api_key: str,
 ) -> dict[str, str]:
-    """Build headers for upstream OpenAI call.
-
-    - Uses server-side OpenAI API key
-    - Does NOT forward inbound Authorization
-    - Forwards safe headers (User-Agent, OpenAI-Organization/Project, etc.)
-    """
-    settings = get_settings()
-    api_key = getattr(settings, "openai_api_key", None)
-    if not api_key:
+    if not openai_api_key:
         raise HTTPException(status_code=500, detail="Server is missing OPENAI_API_KEY")
 
-    outbound: dict[str, str] = {
-        "Authorization": f"Bearer {api_key}",
-    }
-
-    if inbound_headers:
-        passthrough_allow = {
-            "user-agent",
-            "openai-organization",
-            "openai-project",
-            "openai-beta",
-        }
-        for k, v in inbound_headers.items():
-            lk = k.lower()
-            if lk in passthrough_allow:
-                outbound[k] = v
-
-    if content_type:
-        outbound["Content-Type"] = content_type
-    if accept:
-        outbound["Accept"] = accept
-
-    return outbound
-
-
-def _normalize_query_params(query: Optional[Mapping[str, Any]]) -> list[tuple[str, str]]:
-    if not query:
-        return []
-    items: list[tuple[str, str]] = []
-    for k, v in query.items():
-        if v is None:
-            continue
-        if isinstance(v, (list, tuple)):
-            for vv in v:
-                if vv is None:
-                    continue
-                items.append((str(k), str(vv)))
-        else:
-            items.append((str(k), str(v)))
-    return items
-
-
-def _get_timeout_seconds(request: Optional[Request] = None) -> float:
-    """Centralized request timeout selection."""
-    settings = get_settings()
-    timeout = getattr(settings, "proxy_timeout_seconds", None)
-    if timeout is None:
-        timeout = getattr(settings, "relay_timeout_seconds", 120)
-    try:
-        return float(timeout)
-    except Exception:
-        return 120.0
+    out = _filter_inbound_headers(inbound_headers)
 
+    # Upstream auth
+    out["Authorization"] = f"Bearer {openai_api_key}"
 
-def _maybe_model_dump(obj: Any) -> Any:
-    """Convert OpenAI SDK objects to plain JSON-serializable dicts when possible."""
-    if obj is None:
-        return None
+    # Ensure we have a content-type for JSON calls (multipart should already have it)
+    if "content-type" not in {k.lower(): v for k, v in out.items()}:
+        out["Content-Type"] = "application/json"
+
+    # Optional beta headers if configured
+    s = _settings()
+    assistants_beta = getattr(s, "openai_assistants_beta", None)
+    realtime_beta = getattr(s, "openai_realtime_beta", None)
+    if assistants_beta:
+        out["OpenAI-Beta"] = assistants_beta
+    if realtime_beta:
+        out["OpenAI-Beta"] = realtime_beta
+
+    return out
+
+
+def _maybe_model_dump(obj: Any) -> dict[str, Any]:
+    """
+    OpenAI SDK objects are Pydantic-like; support both model_dump() and dict() forms.
+    """
     if hasattr(obj, "model_dump"):
-        try:
-            return obj.model_dump()
-        except Exception:
-            pass
-    if hasattr(obj, "dict"):
-        try:
-            return obj.dict()
-        except Exception:
-            pass
-    return obj
+        return obj.model_dump()  # type: ignore[no-any-return]
+    if isinstance(obj, dict):
+        return obj
+    # Fallback: try json round-trip
+    try:
+        return json.loads(json.dumps(obj, default=str))
+    except Exception:
+        return {"result": str(obj)}
 
 
 # -------------------------
-# Generic passthrough forwarder
+# Generic forwarders (httpx)
 # -------------------------
 
-async def forward_openai_request(request: Request, upstream_path: str) -> Response:
-    """Forward an inbound FastAPI request to OpenAI upstream.
-
-    Supports:
-    - JSON requests
-    - multipart/form-data uploads (streamed)
-    - SSE streaming responses (if upstream returns text/event-stream)
-    - binary responses
+async def forward_openai_request(request: Request) -> Response:
     """
-    upstream_url = build_upstream_url(upstream_path)
-    timeout = _get_timeout_seconds(request)
+    Forward an incoming FastAPI request to the upstream OpenAI API using httpx.
+    This is suitable for:
+      - JSON
+      - multipart/form-data (Uploads/Files)
+      - binary content endpoints (as long as you return Response with correct headers)
+      - SSE streaming (when upstream responds as text/event-stream)
+    """
+    s = _settings()
+    base = getattr(s, "openai_api_base", "https://api.openai.com/v1")
+    key = getattr(s, "openai_api_key", "")
+    timeout_s = float(getattr(s, "proxy_timeout", 120))
 
-    # Decide whether to stream request body
-    content_type = request.headers.get("content-type", "")
-    is_multipart = content_type.startswith("multipart/form-data")
+    upstream_url = join_url(base, request.url.path)
 
-    outbound_headers = build_outbound_headers(
-        request.headers,
-        content_type=None if is_multipart else content_type or None,
-        accept=request.headers.get("accept"),
-    )
+    headers = build_outbound_headers(inbound_headers=request.headers, openai_api_key=key)
 
-    client = get_async_httpx_client()
+    # Preserve query string
+    query = request.url.query
+    if query:
+        upstream_url = upstream_url + "?" + query
 
-    relay_log.info("Forwarding %s %s", request.method, upstream_path)
+    client = get_async_httpx_client(timeout=timeout_s)
 
-    if is_multipart:
-        # Stream body directly to upstream (avoid buffering large uploads)
-        async def body_iter():
-            async for chunk in request.stream():
-                yield chunk
+    # Read body bytes once; forward as-is.
+    body = await request.body()
 
-        upstream_resp = await client.request(
-            method=request.method,
-            url=upstream_url,
-            headers=outbound_headers,
-            params=request.query_params,
-            content=body_iter(),
-            timeout=timeout,
-        )
-    else:
-        raw = await request.body()
-        upstream_resp = await client.request(
-            method=request.method,
-            url=upstream_url,
-            headers=outbound_headers,
-            params=request.query_params,
-            content=raw if raw else None,
-            timeout=timeout,
-        )
+    relay_log.debug("Forwarding %s %s -> %s", request.method, request.url.path, upstream_url)
 
-    media_type = upstream_resp.headers.get("content-type")
+    # Streaming SSE support
+    accept = request.headers.get("accept", "")
+    wants_sse = "text/event-stream" in accept.lower()
 
-    # If SSE, stream it through
-    if media_type and media_type.startswith("text/event-stream"):
-        async def sse_stream():
-            async for line in upstream_resp.aiter_lines():
-                yield (line + "\n").encode("utf-8")
+    if wants_sse:
+        async def event_generator():
+            async with client.stream(
+                request.method,
+                upstream_url,
+                headers=headers,
+                content=body if body else None,
+            ) as upstream_resp:
+                upstream_resp.raise_for_status()
+                async for chunk in upstream_resp.aiter_bytes():
+                    if chunk:
+                        yield chunk
 
         return StreamingResponse(
-            sse_stream(),
-            status_code=upstream_resp.status_code,
-            headers=filter_upstream_headers(upstream_resp.headers),
-            media_type=media_type,
+            event_generator(),
+            status_code=200,
+            media_type="text/event-stream",
         )
 
-    # Otherwise, return buffered content
-    content = await upstream_resp.aread()
+    upstream_resp = await client.request(
+        request.method,
+        upstream_url,
+        headers=headers,
+        content=body if body else None,
+    )
+
+    # Copy response headers except hop-by-hop
+    resp_headers: dict[str, str] = {}
+    for k, v in upstream_resp.headers.items():
+        if k.lower() in _HOP_BY_HOP_HEADERS:
+            continue
+        resp_headers[k] = v
+
     return Response(
-        content=content,
+        content=upstream_resp.content,
         status_code=upstream_resp.status_code,
-        headers=filter_upstream_headers(upstream_resp.headers),
-        media_type=media_type,
+        headers=resp_headers,
+        media_type=upstream_resp.headers.get("content-type"),
     )
 
 
-# -------------------------
-# JSON-envelope proxy helper
-# -------------------------
-
 async def forward_openai_method_path(
     *,
     method: str,
     path: str,
-    request: Optional[Request] = None,
     query: Optional[Mapping[str, Any]] = None,
-    json_body: Optional[Any] = None,
-    body: Optional[Any] = None,
+    json_body: Any = None,
     inbound_headers: Optional[Mapping[str, str]] = None,
-    headers: Optional[Mapping[str, str]] = None,
 ) -> Response:
-    """Forward an OpenAI API call expressed as method + path (+ optional JSON + query).
-
-    This is used by the /v1/proxy route (JSON envelope).
     """
+    Method/path forwarder for Action-friendly JSON envelope calls (/v1/proxy).
+    """
+    s = _settings()
+    base = getattr(s, "openai_api_base", "https://api.openai.com/v1")
+    key = getattr(s, "openai_api_key", "")
+    timeout_s = float(getattr(s, "proxy_timeout", 120))
+
+    upstream_url = join_url(base, path)
+
+    # Merge/encode query parameters
+    if query:
+        # Preserve ordering and repeated keys where possible
+        pairs: list[tuple[str, str]] = []
+        for k, v in query.items():
+            if v is None:
+                continue
+            if isinstance(v, (list, tuple)):
+                for item in v:
+                    pairs.append((str(k), str(item)))
+            else:
+                pairs.append((str(k), str(v)))
+
+        if pairs:
+            parts = urlsplit(upstream_url)
+            existing = parse_qsl(parts.query, keep_blank_values=True)
+            merged = existing + pairs
+            upstream_url = urlunsplit(
+                (parts.scheme, parts.netloc, parts.path, urlencode(merged, doseq=True), parts.fragment)
+            )
+
+    headers = build_outbound_headers(
+        inbound_headers=inbound_headers or {},
+        openai_api_key=key,
+    )
 
-    # Backward-compatible aliases:
-    # - some callers pass `headers=` instead of `inbound_headers=`
-    # - some callers pass `body=` instead of `json_body=`
-    if inbound_headers is None and headers is not None:
-        inbound_headers = headers
-    if inbound_headers is None and request is not None:
-        inbound_headers = request.headers
-    if json_body is None and body is not None:
-        json_body = body
-
-    upstream_url = build_upstream_url(path)
-    timeout = _get_timeout_seconds(request)
-
-    params = _normalize_query_params(query)
-    content_type = "application/json" if json_body is not None else None
-    outbound_headers = build_outbound_headers(inbound_headers, content_type=content_type)
-
-    client = get_async_httpx_client()
-
-    payload_bytes: Optional[bytes] = None
-    if json_body is not None:
-        payload_bytes = json.dumps(json_body).encode("utf-8")
+    client = get_async_httpx_client(timeout=timeout_s)
 
-    relay_log.info("Proxy-forward %s %s", method.upper(), path)
+    relay_log.debug("Forwarding %s %s -> %s", method, path, upstream_url)
 
     upstream_resp = await client.request(
-        method=method.upper(),
-        url=upstream_url,
-        headers=outbound_headers,
-        params=params,
-        content=payload_bytes,
-        timeout=timeout,
+        method,
+        upstream_url,
+        headers=headers,
+        json=json_body,
     )
 
-    media_type = upstream_resp.headers.get("content-type")
-    content = await upstream_resp.aread()
+    resp_headers: dict[str, str] = {}
+    for k, v in upstream_resp.headers.items():
+        if k.lower() in _HOP_BY_HOP_HEADERS:
+            continue
+        resp_headers[k] = v
 
     return Response(
-        content=content,
+        content=upstream_resp.content,
         status_code=upstream_resp.status_code,
-        headers=filter_upstream_headers(upstream_resp.headers),
-        media_type=media_type,
+        headers=resp_headers,
+        media_type=upstream_resp.headers.get("content-type"),
     )
 
 
@@ -319,30 +286,62 @@ async def forward_openai_method_path(
 # Higher-level helpers used by routes
 # -------------------------
 
-async def forward_responses_create(*, request: Request) -> dict[str, Any]:
+async def forward_responses_create(
+    payload: Optional[dict[str, Any]] = None,
+    *,
+    request: Optional[Request] = None,
+) -> dict[str, Any]:
+    """Create a Response via the OpenAI Python SDK.
+
+    Route handlers may call this helper in two ways:
+      1) forward_responses_create(payload_dict)
+      2) forward_responses_create(request=request)
+
+    We support both to keep route code simple (e.g., when a route needs to
+    inspect or mutate the JSON before calling the SDK).
+    """
     client = get_async_openai_client()
-    payload = await request.json()
+
+    if request is not None:
+        payload = await request.json()
+
+    if payload is None:
+        raise HTTPException(status_code=400, detail="Missing JSON payload for /v1/responses")
+
     relay_log.info("Forward /v1/responses via SDK")
     result = await client.responses.create(**payload)
     return _maybe_model_dump(result)
 
 
-async def forward_embeddings_create(*, request: Request) -> dict[str, Any]:
+async def forward_embeddings_create(
+    payload: Optional[dict[str, Any]] = None,
+    *,
+    request: Optional[Request] = None,
+) -> dict[str, Any]:
+    """Create embeddings via the OpenAI Python SDK.
+
+    Accepts either a JSON payload dict or a FastAPI Request.
+    """
     client = get_async_openai_client()
-    payload = await request.json()
+
+    if request is not None:
+        payload = await request.json()
+
+    if payload is None:
+        raise HTTPException(status_code=400, detail="Missing JSON payload for /v1/embeddings")
+
     relay_log.info("Forward /v1/embeddings via SDK")
     result = await client.embeddings.create(**payload)
     return _maybe_model_dump(result)
 
 
-async def forward_files_list(*, request: Request) -> dict[str, Any]:
+async def forward_files_list() -> dict[str, Any]:
     client = get_async_openai_client()
-    params = dict(request.query_params)
-    result = await client.files.list(**params)
+    result = await client.files.list()
     return _maybe_model_dump(result)
 
 
-async def forward_files_create(*, request: Request) -> dict[str, Any]:
+async def forward_files_create() -> dict[str, Any]:
     # Files create is multipart; use generic forwarder path in route (preferred).
     # This helper exists for compatibility with some route variants.
     raise HTTPException(status_code=400, detail="Use multipart passthrough for file uploads")
diff --git a/project-tree.md b/project-tree.md
index 68380ac..7ca54dd 100755
--- a/project-tree.md
+++ b/project-tree.md
@@ -1,4 +1,4 @@
-  📄 .env
+  📄 .env.env
   📄 .env.example.env
   📄 .gitattributes
   📄 .gitignore
@@ -68,10 +68,7 @@
     📄 requires.txt
     📄 top_level.txt
   📁 data
-    📄 conversations.csv
-    📄 conversations.db
     📁 conversations
-      📄 conversations.db
     📁 embeddings
       📄 embeddings.db
     📁 files
@@ -107,5 +104,4 @@
     📄 client.py
     📄 conftest.py
     📄 test_local_e2e.py
-    📄 test_relay_auth_guard.py
-    📁 downloads
\ No newline at end of file
+    📄 test_relay_auth_guard.py
\ No newline at end of file
```

## CURRENT CONTENT OF CHANGED FILES (WORKTREE)

## FILE: app/api/forward_openai.py @ WORKTREE
```
from __future__ import annotations

import json
from typing import Any, Mapping, Optional
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import httpx
from fastapi import HTTPException, Request
from fastapi.responses import Response, StreamingResponse

from app.core.http_client import get_async_httpx_client, get_async_openai_client
from app.utils.logger import relay_log

# Settings access (supports either get_settings() or a module-level settings object).
try:
    from app.core.config import get_settings  # type: ignore
except ImportError:  # pragma: no cover
    get_settings = None  # type: ignore

try:
    from app.core.config import settings as module_settings  # type: ignore
except ImportError:  # pragma: no cover
    module_settings = None  # type: ignore


def _settings() -> Any:
    if get_settings is not None:
        return get_settings()
    if module_settings is not None:
        return module_settings
    raise RuntimeError("Settings not available (expected get_settings() or settings)")


# -------------------------
# Header / URL helpers
# -------------------------

_HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
}


def normalize_base_url(base_url: str) -> str:
    """
    Normalize an OpenAI base URL for consistent join semantics.
    Accepts:
      - https://api.openai.com
      - https://api.openai.com/v1
    Returns a base ending with /v1
    """
    b = (base_url or "").strip()
    if not b:
        raise ValueError("OPENAI_API_BASE is empty")
    b = b.rstrip("/")
    if b.endswith("/v1"):
        return b
    return b + "/v1"


def join_url(base_v1: str, path: str) -> str:
    base_v1 = normalize_base_url(base_v1)
    p = (path or "").strip()
    if not p.startswith("/"):
        p = "/" + p
    # If path already includes /v1, strip it so we don't double it.
    if p.startswith("/v1/"):
        p = p[3:]
    elif p == "/v1":
        p = ""
    return base_v1 + p


def _filter_inbound_headers(headers: Mapping[str, str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for k, v in headers.items():
        lk = k.lower()
        if lk in _HOP_BY_HOP_HEADERS:
            continue
        # Never forward the relay's own Authorization header upstream.
        if lk == "authorization":
            continue
        out[k] = v
    return out


def build_outbound_headers(
    *,
    inbound_headers: Mapping[str, str],
    openai_api_key: str,
) -> dict[str, str]:
    if not openai_api_key:
        raise HTTPException(status_code=500, detail="Server is missing OPENAI_API_KEY")

    out = _filter_inbound_headers(inbound_headers)

    # Upstream auth
    out["Authorization"] = f"Bearer {openai_api_key}"

    # Ensure we have a content-type for JSON calls (multipart should already have it)
    if "content-type" not in {k.lower(): v for k, v in out.items()}:
        out["Content-Type"] = "application/json"

    # Optional beta headers if configured
    s = _settings()
    assistants_beta = getattr(s, "openai_assistants_beta", None)
    realtime_beta = getattr(s, "openai_realtime_beta", None)
    if assistants_beta:
        out["OpenAI-Beta"] = assistants_beta
    if realtime_beta:
        out["OpenAI-Beta"] = realtime_beta

    return out


def _maybe_model_dump(obj: Any) -> dict[str, Any]:
    """
    OpenAI SDK objects are Pydantic-like; support both model_dump() and dict() forms.
    """
    if hasattr(obj, "model_dump"):
        return obj.model_dump()  # type: ignore[no-any-return]
    if isinstance(obj, dict):
        return obj
    # Fallback: try json round-trip
    try:
        return json.loads(json.dumps(obj, default=str))
    except Exception:
        return {"result": str(obj)}


# -------------------------
# Generic forwarders (httpx)
# -------------------------

async def forward_openai_request(request: Request) -> Response:
    """
    Forward an incoming FastAPI request to the upstream OpenAI API using httpx.
    This is suitable for:
      - JSON
      - multipart/form-data (Uploads/Files)
      - binary content endpoints (as long as you return Response with correct headers)
      - SSE streaming (when upstream responds as text/event-stream)
    """
    s = _settings()
    base = getattr(s, "openai_api_base", "https://api.openai.com/v1")
    key = getattr(s, "openai_api_key", "")
    timeout_s = float(getattr(s, "proxy_timeout", 120))

    upstream_url = join_url(base, request.url.path)

    headers = build_outbound_headers(inbound_headers=request.headers, openai_api_key=key)

    # Preserve query string
    query = request.url.query
    if query:
        upstream_url = upstream_url + "?" + query

    client = get_async_httpx_client(timeout=timeout_s)

    # Read body bytes once; forward as-is.
    body = await request.body()

    relay_log.debug("Forwarding %s %s -> %s", request.method, request.url.path, upstream_url)

    # Streaming SSE support
    accept = request.headers.get("accept", "")
    wants_sse = "text/event-stream" in accept.lower()

    if wants_sse:
        async def event_generator():
            async with client.stream(
                request.method,
                upstream_url,
                headers=headers,
                content=body if body else None,
            ) as upstream_resp:
                upstream_resp.raise_for_status()
                async for chunk in upstream_resp.aiter_bytes():
                    if chunk:
                        yield chunk

        return StreamingResponse(
            event_generator(),
            status_code=200,
            media_type="text/event-stream",
        )

    upstream_resp = await client.request(
        request.method,
        upstream_url,
        headers=headers,
        content=body if body else None,
    )

    # Copy response headers except hop-by-hop
    resp_headers: dict[str, str] = {}
    for k, v in upstream_resp.headers.items():
        if k.lower() in _HOP_BY_HOP_HEADERS:
            continue
        resp_headers[k] = v

    return Response(
        content=upstream_resp.content,
        status_code=upstream_resp.status_code,
        headers=resp_headers,
        media_type=upstream_resp.headers.get("content-type"),
    )


async def forward_openai_method_path(
    *,
    method: str,
    path: str,
    query: Optional[Mapping[str, Any]] = None,
    json_body: Any = None,
    inbound_headers: Optional[Mapping[str, str]] = None,
) -> Response:
    """
    Method/path forwarder for Action-friendly JSON envelope calls (/v1/proxy).
    """
    s = _settings()
    base = getattr(s, "openai_api_base", "https://api.openai.com/v1")
    key = getattr(s, "openai_api_key", "")
    timeout_s = float(getattr(s, "proxy_timeout", 120))

    upstream_url = join_url(base, path)

    # Merge/encode query parameters
    if query:
        # Preserve ordering and repeated keys where possible
        pairs: list[tuple[str, str]] = []
        for k, v in query.items():
            if v is None:
                continue
            if isinstance(v, (list, tuple)):
                for item in v:
                    pairs.append((str(k), str(item)))
            else:
                pairs.append((str(k), str(v)))

        if pairs:
            parts = urlsplit(upstream_url)
            existing = parse_qsl(parts.query, keep_blank_values=True)
            merged = existing + pairs
            upstream_url = urlunsplit(
                (parts.scheme, parts.netloc, parts.path, urlencode(merged, doseq=True), parts.fragment)
            )

    headers = build_outbound_headers(
        inbound_headers=inbound_headers or {},
        openai_api_key=key,
    )

    client = get_async_httpx_client(timeout=timeout_s)

    relay_log.debug("Forwarding %s %s -> %s", method, path, upstream_url)

    upstream_resp = await client.request(
        method,
        upstream_url,
        headers=headers,
        json=json_body,
    )

    resp_headers: dict[str, str] = {}
    for k, v in upstream_resp.headers.items():
        if k.lower() in _HOP_BY_HOP_HEADERS:
            continue
        resp_headers[k] = v

    return Response(
        content=upstream_resp.content,
        status_code=upstream_resp.status_code,
        headers=resp_headers,
        media_type=upstream_resp.headers.get("content-type"),
    )


# -------------------------
# Higher-level helpers used by routes
# -------------------------

async def forward_responses_create(
    payload: Optional[dict[str, Any]] = None,
    *,
    request: Optional[Request] = None,
) -> dict[str, Any]:
    """Create a Response via the OpenAI Python SDK.

    Route handlers may call this helper in two ways:
      1) forward_responses_create(payload_dict)
      2) forward_responses_create(request=request)

    We support both to keep route code simple (e.g., when a route needs to
    inspect or mutate the JSON before calling the SDK).
    """
    client = get_async_openai_client()

    if request is not None:
        payload = await request.json()

    if payload is None:
        raise HTTPException(status_code=400, detail="Missing JSON payload for /v1/responses")

    relay_log.info("Forward /v1/responses via SDK")
    result = await client.responses.create(**payload)
    return _maybe_model_dump(result)


async def forward_embeddings_create(
    payload: Optional[dict[str, Any]] = None,
    *,
    request: Optional[Request] = None,
) -> dict[str, Any]:
    """Create embeddings via the OpenAI Python SDK.

    Accepts either a JSON payload dict or a FastAPI Request.
    """
    client = get_async_openai_client()

    if request is not None:
        payload = await request.json()

    if payload is None:
        raise HTTPException(status_code=400, detail="Missing JSON payload for /v1/embeddings")

    relay_log.info("Forward /v1/embeddings via SDK")
    result = await client.embeddings.create(**payload)
    return _maybe_model_dump(result)


async def forward_files_list() -> dict[str, Any]:
    client = get_async_openai_client()
    result = await client.files.list()
    return _maybe_model_dump(result)


async def forward_files_create() -> dict[str, Any]:
    # Files create is multipart; use generic forwarder path in route (preferred).
    # This helper exists for compatibility with some route variants.
    raise HTTPException(status_code=400, detail="Use multipart passthrough for file uploads")


async def forward_files_retrieve(*, file_id: str) -> dict[str, Any]:
    client = get_async_openai_client()
    result = await client.files.retrieve(file_id)
    return _maybe_model_dump(result)


async def forward_files_delete(*, file_id: str) -> dict[str, Any]:
    client = get_async_openai_client()
    result = await client.files.delete(file_id)
    return _maybe_model_dump(result)
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
  📁 static
    📁 .well-known
      📄 __init__.py
      📄 ai-plugin.json
  📁 tests
    📄 __init__.py
    📄 client.py
    📄 conftest.py
    📄 test_local_e2e.py
    📄 test_relay_auth_guard.py```

