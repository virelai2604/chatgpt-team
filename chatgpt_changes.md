# ChatGPT Sync
Repo: chatgpt-team
Base: origin/main
Base commit (merge-base): f26082d70e0df7af1e11fd7f824eb493b1af278a
Dirs: app tests static schemas
Root files: project-tree.md pyproject.toml
Mode: changes
Generated: 2025-12-22T21:08:45+07:00

## CHANGE SUMMARY (since f26082d70e0df7af1e11fd7f824eb493b1af278a, includes worktree)

```
M	app/api/forward_openai.py
M	app/core/http_client.py
```

## PATCH (since f26082d70e0df7af1e11fd7f824eb493b1af278a, includes worktree)

```diff
diff --git a/app/api/forward_openai.py b/app/api/forward_openai.py
index 275aab4..833b5bd 100755
--- a/app/api/forward_openai.py
+++ b/app/api/forward_openai.py
@@ -46,6 +46,13 @@ _HOP_BY_HOP_HEADERS = {
     "upgrade",
 }
 
+# Must not forward these upstream (common relay bug sources)
+_STRIP_REQUEST_HEADERS = {
+    "authorization",    # relay key
+    "host",             # never forward localhost host to OpenAI
+    "content-length",   # let httpx compute it for upstream request
+}
+
 
 def normalize_base_url(base_url: str) -> str:
     """
@@ -77,14 +84,41 @@ def join_url(base_v1: str, path: str) -> str:
     return base_v1 + p
 
 
+# -------------------------
+# Backwards-compat shims
+# -------------------------
+
+def _get_timeout_seconds() -> float:
+    """Return the default upstream timeout in seconds (float)."""
+    s = _settings()
+    raw = getattr(s, "proxy_timeout", None)
+    if raw is None:
+        raw = getattr(s, "openai_timeout", None)
+    try:
+        return float(raw) if raw is not None else 120.0
+    except (TypeError, ValueError):
+        return 120.0
+
+
+def build_upstream_url(path: str) -> str:
+    """Build a fully-qualified OpenAI upstream URL for a given path."""
+    s = _settings()
+    base = getattr(s, "openai_api_base", "https://api.openai.com/v1")
+    return join_url(base, path)
+
+
+def filter_upstream_headers(headers: Mapping[str, str]) -> dict[str, str]:
+    """Filter hop-by-hop headers and relay/transport headers from inbound headers."""
+    return _filter_inbound_headers(headers)
+
+
 def _filter_inbound_headers(headers: Mapping[str, str]) -> dict[str, str]:
     out: dict[str, str] = {}
     for k, v in headers.items():
         lk = k.lower()
         if lk in _HOP_BY_HOP_HEADERS:
             continue
-        # Never forward the relay's own Authorization header upstream.
-        if lk == "authorization":
+        if lk in _STRIP_REQUEST_HEADERS:
             continue
         out[k] = v
     return out
@@ -120,14 +154,11 @@ def build_outbound_headers(
 
 
 def _maybe_model_dump(obj: Any) -> dict[str, Any]:
-    """
-    OpenAI SDK objects are Pydantic-like; support both model_dump() and dict() forms.
-    """
+    """OpenAI SDK objects are Pydantic-like; support model_dump() and dict()."""
     if hasattr(obj, "model_dump"):
         return obj.model_dump()  # type: ignore[no-any-return]
     if isinstance(obj, dict):
         return obj
-    # Fallback: try json round-trip
     try:
         return json.loads(json.dumps(obj, default=str))
     except Exception:
@@ -141,11 +172,11 @@ def _maybe_model_dump(obj: Any) -> dict[str, Any]:
 async def forward_openai_request(request: Request) -> Response:
     """
     Forward an incoming FastAPI request to the upstream OpenAI API using httpx.
-    This is suitable for:
+    Suitable for:
       - JSON
       - multipart/form-data (Uploads/Files)
-      - binary content endpoints (as long as you return Response with correct headers)
-      - SSE streaming (when upstream responds as text/event-stream)
+      - binary content endpoints
+      - SSE streaming (when client sets Accept: text/event-stream)
     """
     s = _settings()
     base = getattr(s, "openai_api_base", "https://api.openai.com/v1")
@@ -154,23 +185,23 @@ async def forward_openai_request(request: Request) -> Response:
 
     upstream_url = join_url(base, request.url.path)
 
-    headers = build_outbound_headers(inbound_headers=request.headers, openai_api_key=key)
-
     # Preserve query string
     query = request.url.query
     if query:
         upstream_url = upstream_url + "?" + query
 
-    client = get_async_httpx_client(timeout=timeout_s)
-
     # Read body bytes once; forward as-is.
     body = await request.body()
 
+    headers = build_outbound_headers(inbound_headers=request.headers, openai_api_key=key)
+
     relay_log.debug("Forwarding %s %s -> %s", request.method, request.url.path, upstream_url)
 
+    client = get_async_httpx_client(timeout=timeout_s)
+
     # Streaming SSE support
     accept = request.headers.get("accept", "")
-    wants_sse = "text/event-stream" in accept.lower()
+    wants_sse = "text/event-stream" in (accept or "").lower()
 
     if wants_sse:
         async def event_generator():
@@ -180,6 +211,7 @@ async def forward_openai_request(request: Request) -> Response:
                 headers=headers,
                 content=body if body else None,
             ) as upstream_resp:
+                # If upstream errors, it will generally send JSON or text; raising is fine here.
                 upstream_resp.raise_for_status()
                 async for chunk in upstream_resp.aiter_bytes():
                     if chunk:
@@ -198,7 +230,6 @@ async def forward_openai_request(request: Request) -> Response:
         content=body if body else None,
     )
 
-    # Copy response headers except hop-by-hop
     resp_headers: dict[str, str] = {}
     for k, v in upstream_resp.headers.items():
         if k.lower() in _HOP_BY_HOP_HEADERS:
@@ -233,7 +264,6 @@ async def forward_openai_method_path(
 
     # Merge/encode query parameters
     if query:
-        # Preserve ordering and repeated keys where possible
         pairs: list[tuple[str, str]] = []
         for k, v in query.items():
             if v is None:
@@ -291,15 +321,6 @@ async def forward_responses_create(
     *,
     request: Optional[Request] = None,
 ) -> dict[str, Any]:
-    """Create a Response via the OpenAI Python SDK.
-
-    Route handlers may call this helper in two ways:
-      1) forward_responses_create(payload_dict)
-      2) forward_responses_create(request=request)
-
-    We support both to keep route code simple (e.g., when a route needs to
-    inspect or mutate the JSON before calling the SDK).
-    """
     client = get_async_openai_client()
 
     if request is not None:
@@ -318,10 +339,6 @@ async def forward_embeddings_create(
     *,
     request: Optional[Request] = None,
 ) -> dict[str, Any]:
-    """Create embeddings via the OpenAI Python SDK.
-
-    Accepts either a JSON payload dict or a FastAPI Request.
-    """
     client = get_async_openai_client()
 
     if request is not None:
@@ -342,8 +359,6 @@ async def forward_files_list() -> dict[str, Any]:
 
 
 async def forward_files_create() -> dict[str, Any]:
-    # Files create is multipart; use generic forwarder path in route (preferred).
-    # This helper exists for compatibility with some route variants.
     raise HTTPException(status_code=400, detail="Use multipart passthrough for file uploads")
 
 
diff --git a/app/core/http_client.py b/app/core/http_client.py
index feb7102..298d4aa 100644
--- a/app/core/http_client.py
+++ b/app/core/http_client.py
@@ -1,7 +1,7 @@
 from __future__ import annotations
 
 import asyncio
-from typing import Any, Dict, Tuple
+from typing import Dict, Optional, Tuple
 
 import httpx
 from openai import AsyncOpenAI
@@ -11,8 +11,10 @@ from app.utils.logger import get_logger
 
 log = get_logger(__name__)
 
-# Cache per-event-loop to avoid "attached to a different loop" issues with reload.
-_LOOP_CLIENTS: Dict[int, Tuple[httpx.AsyncClient, AsyncOpenAI]] = {}
+# Cache per-event-loop AND per-timeout to avoid:
+# - "attached to a different loop" issues with reload
+# - unintended timeout coupling between routes (SSE vs non-SSE)
+_LOOP_CLIENTS: Dict[Tuple[int, float], Tuple[httpx.AsyncClient, AsyncOpenAI]] = {}
 
 
 def _loop_id() -> int:
@@ -23,52 +25,73 @@ def _loop_id() -> int:
         return -1
 
 
-def get_async_httpx_client() -> httpx.AsyncClient:
-    loop_key = _loop_id()
-    if loop_key in _LOOP_CLIENTS:
-        return _LOOP_CLIENTS[loop_key][0]
+def _normalize_timeout_seconds(timeout_s: float) -> float:
+    # Make float keys stable (avoid 120 vs 120.0 vs 120.0000001)
+    return float(f"{float(timeout_s):.6f}")
+
 
+def get_async_httpx_client(timeout: Optional[float] = None) -> httpx.AsyncClient:
     settings = get_settings()
-    timeout = httpx.Timeout(getattr(settings, "relay_timeout_seconds", 120.0))
-    client = httpx.AsyncClient(timeout=timeout)
+    effective_timeout = (
+        float(timeout)
+        if timeout is not None
+        else float(getattr(settings, "proxy_timeout_seconds", 120.0))
+    )
+    effective_timeout = _normalize_timeout_seconds(effective_timeout)
+
+    key = (_loop_id(), effective_timeout)
+    if key in _LOOP_CLIENTS:
+        return _LOOP_CLIENTS[key][0]
+
+    client_timeout = httpx.Timeout(effective_timeout)
+    client = httpx.AsyncClient(timeout=client_timeout)
+
     openai_client = AsyncOpenAI(
         api_key=settings.openai_api_key,
         base_url=settings.openai_base_url,
         http_client=client,
     )
-    _LOOP_CLIENTS[loop_key] = (client, openai_client)
+
+    _LOOP_CLIENTS[key] = (client, openai_client)
     return client
 
 
-def get_async_openai_client() -> AsyncOpenAI:
-    loop_key = _loop_id()
-    if loop_key in _LOOP_CLIENTS:
-        return _LOOP_CLIENTS[loop_key][1]
+def get_async_openai_client(timeout: Optional[float] = None) -> AsyncOpenAI:
+    settings = get_settings()
+    effective_timeout = (
+        float(timeout)
+        if timeout is not None
+        else float(getattr(settings, "proxy_timeout_seconds", 120.0))
+    )
+    effective_timeout = _normalize_timeout_seconds(effective_timeout)
+
+    key = (_loop_id(), effective_timeout)
+    if key in _LOOP_CLIENTS:
+        return _LOOP_CLIENTS[key][1]
 
     # Ensure both are created together (shared httpx client)
-    get_async_httpx_client()
-    return _LOOP_CLIENTS[loop_key][1]
+    get_async_httpx_client(timeout=effective_timeout)
+    return _LOOP_CLIENTS[key][1]
 
 
 async def close_async_clients() -> None:
-    """Close the cached clients for the current event loop."""
+    """Close the cached clients for the current event loop (all timeouts)."""
     loop_key = _loop_id()
-    if loop_key not in _LOOP_CLIENTS:
-        return
-
-    client, _ = _LOOP_CLIENTS.pop(loop_key)
-    try:
-        await client.aclose()
-    except Exception:
-        log.exception("Failed closing httpx client")
+    keys = [k for k in _LOOP_CLIENTS.keys() if k[0] == loop_key]
+    for k in keys:
+        client, _ = _LOOP_CLIENTS.pop(k)
+        try:
+            await client.aclose()
+        except Exception:
+            log.exception("Failed closing httpx client (loop=%s, timeout=%s)", k[0], k[1])
 
 
 async def aclose_all_clients() -> None:
     """Close all cached clients across loops (best-effort)."""
     items = list(_LOOP_CLIENTS.items())
     _LOOP_CLIENTS.clear()
-    for _, (client, _) in items:
+    for (loop_id, timeout_s), (client, _) in items:
         try:
             await client.aclose()
         except Exception:
-            log.exception("Failed closing httpx client")
+            log.exception("Failed closing httpx client (loop=%s, timeout=%s)", loop_id, timeout_s)
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

# Must not forward these upstream (common relay bug sources)
_STRIP_REQUEST_HEADERS = {
    "authorization",    # relay key
    "host",             # never forward localhost host to OpenAI
    "content-length",   # let httpx compute it for upstream request
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


# -------------------------
# Backwards-compat shims
# -------------------------

def _get_timeout_seconds() -> float:
    """Return the default upstream timeout in seconds (float)."""
    s = _settings()
    raw = getattr(s, "proxy_timeout", None)
    if raw is None:
        raw = getattr(s, "openai_timeout", None)
    try:
        return float(raw) if raw is not None else 120.0
    except (TypeError, ValueError):
        return 120.0


def build_upstream_url(path: str) -> str:
    """Build a fully-qualified OpenAI upstream URL for a given path."""
    s = _settings()
    base = getattr(s, "openai_api_base", "https://api.openai.com/v1")
    return join_url(base, path)


def filter_upstream_headers(headers: Mapping[str, str]) -> dict[str, str]:
    """Filter hop-by-hop headers and relay/transport headers from inbound headers."""
    return _filter_inbound_headers(headers)


def _filter_inbound_headers(headers: Mapping[str, str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for k, v in headers.items():
        lk = k.lower()
        if lk in _HOP_BY_HOP_HEADERS:
            continue
        if lk in _STRIP_REQUEST_HEADERS:
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
    """OpenAI SDK objects are Pydantic-like; support model_dump() and dict()."""
    if hasattr(obj, "model_dump"):
        return obj.model_dump()  # type: ignore[no-any-return]
    if isinstance(obj, dict):
        return obj
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
    Suitable for:
      - JSON
      - multipart/form-data (Uploads/Files)
      - binary content endpoints
      - SSE streaming (when client sets Accept: text/event-stream)
    """
    s = _settings()
    base = getattr(s, "openai_api_base", "https://api.openai.com/v1")
    key = getattr(s, "openai_api_key", "")
    timeout_s = float(getattr(s, "proxy_timeout", 120))

    upstream_url = join_url(base, request.url.path)

    # Preserve query string
    query = request.url.query
    if query:
        upstream_url = upstream_url + "?" + query

    # Read body bytes once; forward as-is.
    body = await request.body()

    headers = build_outbound_headers(inbound_headers=request.headers, openai_api_key=key)

    relay_log.debug("Forwarding %s %s -> %s", request.method, request.url.path, upstream_url)

    client = get_async_httpx_client(timeout=timeout_s)

    # Streaming SSE support
    accept = request.headers.get("accept", "")
    wants_sse = "text/event-stream" in (accept or "").lower()

    if wants_sse:
        async def event_generator():
            async with client.stream(
                request.method,
                upstream_url,
                headers=headers,
                content=body if body else None,
            ) as upstream_resp:
                # If upstream errors, it will generally send JSON or text; raising is fine here.
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

## FILE: app/core/http_client.py @ WORKTREE
```
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

