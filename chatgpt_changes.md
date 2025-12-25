# ChatGPT Sync
Repo: chatgpt-team
Base: origin/main
Base commit (merge-base): 5abeca87377ca8c17d723bad85fd5852dfe7ce89
Dirs: app tests static schemas src scripts/src
Root files: project-tree.md pyproject.toml chatgpt_sync.sh AGENTS.md __init__.py generate_tree.py
Mode: changes
Generated: 2025-12-25T22:37:53+07:00

## CHANGE SUMMARY (since 5abeca87377ca8c17d723bad85fd5852dfe7ce89, includes worktree)

```
M	app/api/forward_openai.py
M	app/api/sse.py
M	app/api/tools_api.py
M	app/core/config.py
M	app/core/http_client.py
M	app/http_client.py
M	app/main.py
M	app/middleware/relay_auth.py
M	app/routes/images.py
M	app/routes/uploads.py
M	app/utils/authy.py
```

## PATCH (since 5abeca87377ca8c17d723bad85fd5852dfe7ce89, includes worktree)

```diff
diff --git a/app/api/forward_openai.py b/app/api/forward_openai.py
index 72097e8..ead4fe0 100755
--- a/app/api/forward_openai.py
+++ b/app/api/forward_openai.py
@@ -26,47 +26,38 @@ _HOP_BY_HOP_HEADERS = {
     "trailers",
     "transfer-encoding",
     "upgrade",
-    "host",
-    "content-length",
 }
 
-# We strip Content-Encoding because the relay requests identity upstream and/or
-# returns decoded bytes. Keeping Content-Encoding while returning identity bytes
-# can break downstream clients (e.g., requests json()).
 _STRIP_RESPONSE_HEADERS = {
     *_HOP_BY_HOP_HEADERS,
     "content-encoding",
+    "content-length",
 }
 
 
 def _get_setting(settings: object, *names: str, default=None):
-    """Return the first non-empty attribute among several possible setting names."""
     for name in names:
         if hasattr(settings, name):
             val = getattr(settings, name)
-            if val is not None and str(val).strip() != "":
+            if val is not None:
                 return val
     return default
 
 
-def _openai_base_url(settings: object) -> str:
-    return str(
-        _get_setting(
-            settings,
-            "OPENAI_BASE_URL",
-            "OPENAI_API_BASE",
-            "openai_base_url",
-            "openai_api_base",
-            default="https://api.openai.com/v1",
-        )
-    ).rstrip("/")
+def _openai_api_key(settings: object) -> str:
+    return str(_get_setting(settings, "OPENAI_API_KEY", "openai_api_key", default="")).strip()
 
 
-def _openai_api_key(settings: object) -> str:
-    key = _get_setting(settings, "OPENAI_API_KEY", "openai_api_key", default="")
-    if not key:
-        raise RuntimeError("OPENAI_API_KEY is not configured.")
-    return str(key)
+def _openai_base_url(settings: object) -> str:
+    # Accept either OPENAI_API_BASE (includes /v1) or OPENAI_BASE_URL (no /v1).
+    api_base = str(_get_setting(settings, "OPENAI_API_BASE", "openai_api_base", default="")).strip()
+    base_url = str(_get_setting(settings, "OPENAI_BASE_URL", "openai_base_url", default="")).strip()
+
+    if api_base:
+        return api_base
+    if base_url:
+        return base_url.rstrip("/") + "/v1"
+    return "https://api.openai.com/v1"
 
 
 def _join_url(base: str, path: str) -> str:
@@ -78,11 +69,12 @@ def _join_url(base: str, path: str) -> str:
     return base + path
 
 
-def _get_timeout_seconds(settings: object) -> float:
+def _get_timeout_seconds(settings: Optional[object] = None) -> float:
     """Compatibility helper used by some route modules."""
+    s = settings or get_settings()
     return float(
         _get_setting(
-            settings,
+            s,
             "PROXY_TIMEOUT_SECONDS",
             "proxy_timeout_seconds",
             "PROXY_TIMEOUT",
@@ -121,47 +113,46 @@ def build_outbound_headers(
     content_type: Optional[str] = None,
     forward_accept: bool = True,
     accept: Optional[str] = None,
-    accept_encoding: str = "identity",
-    path_hint: Optional[str] = None,  # compatibility; not used
 ) -> Dict[str, str]:
     """
-    Build upstream request headers.
-
-    Key behavior:
-      - Never forward client Authorization upstream.
-      - Never forward client Accept-Encoding upstream.
-      - Force relay's server-side OpenAI API key.
-      - Default Accept-Encoding to identity to avoid brotli/br responses that
-        some clients cannot decode.
+    Build outbound headers for an upstream OpenAI call.
+
+    - Drops hop-by-hop headers
+    - Forces Authorization to our configured OpenAI key
+    - Optionally forwards Accept
+    - Adds OpenAI-Organization / OpenAI-Project / OpenAI-Beta when configured
     """
     s = get_settings()
-
     out: Dict[str, str] = {}
 
     for k, v in inbound_headers.items():
         lk = k.lower()
-
         if lk in _HOP_BY_HOP_HEADERS:
             continue
         if lk == "authorization":
             continue
-        if lk == "accept-encoding":
-            continue
-
-        # We'll set Accept/Content-Type explicitly below.
-        if lk == "accept":
-            continue
         if lk == "content-type":
-            # Preserve multipart boundary etc unless caller overrides.
-            if content_type is None:
-                out[k] = v
             continue
-
+        if lk == "accept" and not forward_accept:
+            continue
         out[k] = v
 
-    # Force upstream OpenAI key.
+    # Force our Authorization header (Bearer).
     out["Authorization"] = f"Bearer {_openai_api_key(s)}"
 
+    if forward_accept:
+        if accept:
+            out["Accept"] = accept
+        elif "accept" in {k.lower() for k in inbound_headers.keys()}:
+            # Preserve original case version if present
+            for k, v in inbound_headers.items():
+                if k.lower() == "accept":
+                    out["Accept"] = v
+                    break
+
+    if content_type:
+        out["Content-Type"] = content_type
+
     # Optional org/project/beta headers from config.
     org = _get_setting(s, "OPENAI_ORG", "OPENAI_ORGANIZATION", "openai_organization", default=None)
     if org:
@@ -175,27 +166,16 @@ def build_outbound_headers(
     if beta:
         out["OpenAI-Beta"] = str(beta)
 
-    # Accept header
-    if forward_accept:
-        inbound_accept = None
-        try:
-            inbound_accept = inbound_headers.get("accept")  # type: ignore[attr-defined]
-        except Exception:
-            inbound_accept = None
-        out["Accept"] = accept or inbound_accept or "*/*"
-
-    # Critical: avoid br/brotli unless we can guarantee decode support everywhere.
-    out["Accept-Encoding"] = accept_encoding
-
-    # Content-Type override (when caller explicitly sets it).
-    if content_type is not None and content_type.strip() != "":
-        out["Content-Type"] = content_type
-
     return out
 
 
 def filter_upstream_headers(up_headers: httpx.Headers) -> Dict[str, str]:
-    """Filter upstream response headers to forward back to the client safely."""
+    """
+    Filter response headers from upstream to return to the client.
+
+    - Strips hop-by-hop headers
+    - Strips content-encoding/content-length because we may decompress/re-chunk
+    """
     out: Dict[str, str] = {}
     for k, v in up_headers.items():
         lk = k.lower()
@@ -205,273 +185,103 @@ def filter_upstream_headers(up_headers: httpx.Headers) -> Dict[str, str]:
     return out
 
 
-def _maybe_model_dump(obj: Any) -> Any:
-    if hasattr(obj, "model_dump"):
-        return obj.model_dump()
-    if hasattr(obj, "dict"):
-        return obj.dict()
-    return obj
-
-
-# ---------------------------------------------------------------------------
-# Response body hardening (defensive decoding)
-# ---------------------------------------------------------------------------
-
-_JSON_FIRST_BYTES = set(b'{["-0123456789tfn')
-
-
-def _looks_like_json(data: bytes) -> bool:
-    if not data:
-        return False
-    i = 0
-    ln = len(data)
-    while i < ln and data[i] in b" \t\r\n":
-        i += 1
-    if i >= ln:
-        return False
-    return data[i] in _JSON_FIRST_BYTES
-
-
-def _decode_content_by_encoding(data: bytes, encoding: str) -> bytes:
-    """
-    Best-effort decode for common HTTP Content-Encoding values.
-
-    Note: In normal operation we request Accept-Encoding: identity upstream and/or rely on httpx to decode.
-    This helper exists only as a defensive fallback for misbehaving proxies.
-    """
-    if not data:
-        return data
-
-    # Multiple encodings can be comma-separated; decode in reverse application order.
-    encs = [e.strip().lower() for e in (encoding or "").split(",") if e.strip()]
-    if not encs:
-        return data
-
-    for enc in reversed(encs):
-        if enc in {"identity", "none"}:
-            continue
+def _maybe_decompress(body: bytes, encoding: Optional[str]) -> bytes:
+    enc = (encoding or "").lower().strip()
+    if not body or not enc:
+        return body
+    if enc == "gzip":
+        return gzip.decompress(body)
+    if enc == "deflate":
+        try:
+            return zlib.decompress(body)
+        except zlib.error:
+            return zlib.decompress(body, -zlib.MAX_WBITS)
+    return body
 
-        if enc == "gzip":
-            try:
-                data = gzip.decompress(data)
-                continue
-            except Exception:
-                # Some servers lie and send zlib-wrapped deflate with gzip header.
-                try:
-                    data = zlib.decompress(data, wbits=16 + zlib.MAX_WBITS)
-                    continue
-                except Exception:
-                    return data
-
-        if enc == "deflate":
-            # Try zlib-wrapped first, then raw deflate.
-            try:
-                data = zlib.decompress(data)
-                continue
-            except Exception:
-                try:
-                    data = zlib.decompress(data, wbits=-zlib.MAX_WBITS)
-                    continue
-                except Exception:
-                    return data
-
-        if enc == "br":
-            # Optional dependency; only decode if available.
-            brotli = None
-            try:
-                import brotli as brotli_lib  # type: ignore
-                brotli = brotli_lib
-            except Exception:
-                try:
-                    import brotlicffi as brotli_lib  # type: ignore
-                    brotli = brotli_lib
-                except Exception:
-                    brotli = None
-
-            if brotli is None:
-                return data
-
-            try:
-                data = brotli.decompress(data)  # type: ignore[attr-defined]
-                continue
-            except Exception:
-                return data
-
-        # Unknown encoding: bail out.
-        return data
-
-    return data
 
+async def _read_response_bytes(resp: httpx.Response) -> bytes:
+    return await resp.aread()
 
-# ---------------------------------------------------------------------------
-# Core forwarders
-# ---------------------------------------------------------------------------
 
-async def forward_openai_request(request: Request) -> Response:
+async def forward_openai_request(
+    request: Request,
+    *,
+    method: str,
+    path: str,
+    json_body: Optional[Any] = None,
+    data: Optional[bytes] = None,
+    content_type: Optional[str] = None,
+    accept: Optional[str] = None,
+    stream: bool = False,
+) -> Response:
     """
-    Raw HTTP passthrough to the upstream OpenAI API.
+    Forward an inbound FastAPI request to upstream OpenAI, returning a FastAPI Response.
 
     Supports:
-      - JSON + multipart requests
-      - SSE streaming when upstream returns text/event-stream
-
-    Hardening:
-      - Forces Accept-Encoding=identity upstream (avoids brotli responses that
-        break some clients / test harnesses).
-      - Never raises on upstream non-2xx; returns upstream status + body.
+      - JSON requests
+      - raw bytes requests (for specific endpoints)
+      - streaming (SSE) passthrough when `stream=True`
     """
-    upstream_url = build_upstream_url(request.url.path, request=request)
+    s = get_settings()
+    timeout_s = _get_timeout_seconds(s)
+    http_client = get_async_httpx_client(timeout=timeout_s)
 
-    # Preserve inbound Content-Type unless caller wants to override; this keeps
-    # multipart boundaries intact.
+    url = build_upstream_url(path, request=request, base_url=_openai_base_url(s))
     headers = build_outbound_headers(
-        inbound_headers=request.headers,
-        content_type=None,
+        inbound_headers=dict(request.headers),
+        content_type=content_type,
         forward_accept=True,
-        accept_encoding="identity",
-    )
-
-    # Only send a body for methods that can carry one.
-    body_bytes: Optional[bytes]
-    if request.method.upper() in {"GET", "HEAD"}:
-        body_bytes = None
-    else:
-        body_bytes = await request.body()
-
-    timeout_s = _get_timeout_seconds(get_settings())
-    client = get_async_httpx_client(timeout=timeout_s)
-
-    upstream_req = client.build_request(
-        method=request.method.upper(),
-        url=upstream_url,
-        headers=headers,
-        content=body_bytes,
+        accept=accept,
     )
 
-    upstream = await client.send(upstream_req, stream=True)
-    media_type = upstream.headers.get("content-type")
-
-    # SSE streaming
-    if media_type and "text/event-stream" in media_type.lower():
-
-        async def gen() -> AsyncIterator[bytes]:
-            try:
-                async for chunk in upstream.aiter_bytes():
-                    yield chunk
-            finally:
-                await upstream.aclose()
+    if stream:
+        async def iter_bytes() -> AsyncIterator[bytes]:
+            async with http_client.stream(method, url, headers=headers, json=json_body, content=data) as resp:
+                resp.raise_for_status()
+                async for chunk in resp.aiter_bytes():
+                    if chunk:
+                        yield chunk
 
         return StreamingResponse(
-            gen(),
-            status_code=upstream.status_code,
-            headers=filter_upstream_headers(upstream.headers),
-            media_type=media_type,
+            iter_bytes(),
+            status_code=200,
+            headers={},  # SSE route typically controls headers separately
+            media_type="text/event-stream",
         )
 
-    # Non-SSE: return buffered content (small JSON payloads, errors, etc.)
-    try:
-        data = await upstream.aread()
-    finally:
-        await upstream.aclose()
+    resp = await http_client.request(method, url, headers=headers, json=json_body, content=data)
+    raw = await _read_response_bytes(resp)
 
-    # Defensive: if upstream still returns encoded bytes (rare), try to decode.
-    content_encoding = upstream.headers.get("content-encoding") or ""
-    if content_encoding and media_type and "application/json" in media_type.lower():
-        if not _looks_like_json(data):
-            data = _decode_content_by_encoding(data, content_encoding)
+    decompressed = _maybe_decompress(raw, resp.headers.get("content-encoding"))
+    out_headers = filter_upstream_headers(resp.headers)
 
     return Response(
-        content=data,
-        status_code=upstream.status_code,
-        headers=filter_upstream_headers(upstream.headers),
-        media_type=media_type,
+        content=decompressed,
+        status_code=resp.status_code,
+        headers=out_headers,
+        media_type=resp.headers.get("content-type"),
     )
 
 
-async def forward_openai_method_path(
-    method: str,
-    path: str,
-    request: Optional[Request] = None,
-    *,
-    query: Optional[Mapping[str, Any]] = None,
-    json_body: Optional[Any] = None,
-    body: Optional[Any] = None,
-    inbound_headers: Optional[Mapping[str, str]] = None,
-) -> Response:
+def forward_openai_method_path(method: str, path: str):
     """
-    JSON-focused forwarder used by /v1/proxy and a few compatibility routes.
-
-    Supports multiple call styles that exist in the codebase:
-      - forward_openai_method_path("POST", "/v1/videos", request)
-      - forward_openai_method_path(method="POST", path="/v1/responses", query=..., json_body=..., inbound_headers=...)
+    Small adapter used by action-friendly proxy routes.
+    Returns (method_upper, normalized_path).
     """
-    s = get_settings()
-    base_url = _openai_base_url(s)
-    url = _join_url(base_url, path)
-
-    if query:
-        url = url + "?" + urlencode(query, doseq=True)
-
-    headers_source: Mapping[str, str]
-    if inbound_headers is not None:
-        headers_source = inbound_headers
-    elif request is not None:
-        headers_source = request.headers
-    else:
-        headers_source = {}
-
-    # Prefer json_body, fall back to body for legacy callers.
-    payload = json_body if json_body is not None else body
-
-    content: Optional[bytes] = None
-    content_type: Optional[str] = None
-
-    m = method.strip().upper()
-    if m not in {"GET", "HEAD"}:
-        if payload is None:
-            content = None
-        elif isinstance(payload, (bytes, bytearray)):
-            content = bytes(payload)
-        else:
-            content = json.dumps(payload).encode("utf-8")
-            content_type = "application/json"
-
-    headers = build_outbound_headers(
-        inbound_headers=headers_source,
-        content_type=content_type,
-        forward_accept=True,
-        accept_encoding="identity",
-    )
-
-    timeout_s = _get_timeout_seconds(s)
-    client = get_async_httpx_client(timeout=timeout_s)
-    upstream = await client.request(m, url, headers=headers, content=content)
+    m = (method or "").upper().strip()
+    p = "/" + (path or "").lstrip("/")
+    return m, p
 
-    data = upstream.content
-    media_type = upstream.headers.get("content-type")
-    content_encoding = upstream.headers.get("content-encoding") or ""
-    if content_encoding and media_type and "application/json" in media_type.lower():
-        if not _looks_like_json(data):
-            data = _decode_content_by_encoding(data, content_encoding)
-
-    return Response(
-        content=data,
-        status_code=upstream.status_code,
-        headers=filter_upstream_headers(upstream.headers),
-        media_type=media_type,
-    )
 
+def _maybe_model_dump(obj: Any) -> Any:
+    # OpenAI SDK objects often implement model_dump(); if not, return as-is.
+    dump = getattr(obj, "model_dump", None)
+    if callable(dump):
+        return dump()
+    return obj
 
-# ---------------------------------------------------------------------------
-# Typed helpers (openai-python SDK)
-# ---------------------------------------------------------------------------
 
 async def forward_responses_create(payload: Dict[str, Any]) -> Any:
-    """
-    Typed helper for non-streaming /v1/responses.
-
-    Some routers import this symbol directly (keep stable).
-    """
     client = get_async_openai_client()
     result = await client.responses.create(**payload)
     return _maybe_model_dump(result)
@@ -483,8 +293,36 @@ async def forward_embeddings_create(payload: Dict[str, Any]) -> Any:
     return _maybe_model_dump(result)
 
 
+# ---------------------------------------------------------------------------
+# Legacy helper names (kept for backwards compatibility with older route code)
+# ---------------------------------------------------------------------------
+
+def _join_upstream_url(base: str, path: str, query: str) -> str:
+    """Join base+path and append a pre-encoded query string, avoiding /v1 duplication."""
+    url = _join_url(base, path)
+    q = (query or "").lstrip("?")
+    return f"{url}?{q}" if q else url
+
+
+def _build_outbound_headers(in_headers: Any) -> Dict[str, str]:
+    """Compatibility wrapper for routes that pass `request.headers.items()`."""
+    try:
+        inbound = {str(k): str(v) for k, v in in_headers}
+    except Exception:
+        inbound = dict(in_headers) if in_headers is not None else {}
+    return build_outbound_headers(inbound_headers=inbound)
+
+
+def _filter_response_headers(up_headers: httpx.Headers) -> Dict[str, str]:
+    """Compatibility wrapper for filtering upstream response headers."""
+    return filter_upstream_headers(up_headers)
+
+
 __all__ = [
     "_get_timeout_seconds",
+    "_join_upstream_url",
+    "_build_outbound_headers",
+    "_filter_response_headers",
     "build_outbound_headers",
     "build_upstream_url",
     "filter_upstream_headers",
diff --git a/app/api/sse.py b/app/api/sse.py
index 7987381..2b74114 100644
--- a/app/api/sse.py
+++ b/app/api/sse.py
@@ -1,98 +1,78 @@
-# app/api/sse.py
 from __future__ import annotations
 
 import json
-from typing import Any, AsyncIterator, Dict, Iterable, Optional, Union
-
-from fastapi import APIRouter, Body
-from fastapi.responses import StreamingResponse
-
-from app.core.http_client import get_async_openai_client
-from app.utils.logger import get_logger
-
-logger = get_logger(__name__)
-
-router = APIRouter(prefix="/v1", tags=["openai-relay-streaming"])
-
-SSEByteSource = Union[Iterable[bytes], AsyncIterator[bytes]]
-
-
-def format_sse_event(
-    *,
-    event: str,
-    data: str,
-    id: Optional[str] = None,
-    retry: Optional[int] = None,
-) -> bytes:
-    lines = []
-    if id is not None:
-        lines.append(f"id: {id}")
-    if event:
-        lines.append(f"event: {event}")
-
-    if data == "":
-        lines.append("data:")
-    else:
-        for line in data.splitlines():
-            lines.append(f"data: {line}")
-
-    if retry is not None:
-        lines.append(f"retry: {retry}")
-
-    payload = "\n".join(lines) + "\n\n"
-    return payload.encode("utf-8")
-
-
-def sse_error_event(message: str, code: Optional[str] = None, *, id: Optional[str] = None) -> bytes:
-    payload = {"message": message}
-    if code:
-        payload["code"] = code
-    data_str = ";".join([f"{k}={v}" for k, v in payload.items()])
-    return format_sse_event(event="error", data=data_str, id=id)
-
-
-class StreamingSSE(StreamingResponse):
-    def __init__(self, content: SSEByteSource, status_code: int = 200, headers: Optional[dict] = None) -> None:
-        super().__init__(content=content, status_code=status_code, headers=headers, media_type="text/event-stream")
-
-
-# Compatibility shim: some older modules imported create_sse_stream from app.api.sse
-def create_sse_stream(
-    content: SSEByteSource,
-    *,
-    status_code: int = 200,
-    headers: Optional[dict] = None,
-) -> StreamingSSE:
-    return StreamingSSE(content=content, status_code=status_code, headers=headers)
-
-
-async def _responses_event_stream(payload: Dict[str, Any]) -> AsyncIterator[bytes]:
-    client = get_async_openai_client()
-    logger.info("Streaming /v1/responses:stream with payload: %s", payload)
-
-    p = dict(payload)
-    p.setdefault("stream", True)
-
-    stream = await client.responses.create(**p)  # stream=True above
-
-    async for event in stream:
-        if hasattr(event, "model_dump_json"):
-            data_json = event.model_dump_json()
-        elif hasattr(event, "model_dump"):
-            data_json = json.dumps(event.model_dump(), default=str, separators=(",", ":"))
-        else:
-            try:
-                data_json = json.dumps(event, default=str, separators=(",", ":"))
-            except TypeError:
-                data_json = json.dumps(str(event))
-
-        yield f"data: {data_json}\n\n".encode("utf-8")
-
-    yield b"data: [DONE]\n\n"
-
-
-@router.post("/responses:stream")
-async def responses_stream(
-    body: Dict[str, Any] = Body(..., description="OpenAI Responses.create payload for streaming"),
-) -> StreamingSSE:
-    return StreamingSSE(_responses_event_stream(body))
+from typing import Any, Dict
+
+import httpx
+from fastapi import APIRouter, Request
+from starlette.responses import JSONResponse, Response, StreamingResponse
+
+from app.core.config import settings
+from app.core.http_client import get_async_httpx_client
+from app.api.forward_openai import _build_outbound_headers, _filter_response_headers, _join_upstream_url  # type: ignore
+from app.utils.logger import relay_log as logger
+
+router = APIRouter(prefix="/v1", tags=["sse"])
+
+
+@router.post("/responses:stream", include_in_schema=False)
+async def responses_stream(request: Request) -> Response:
+    """
+    Compatibility endpoint used by your tests.
+
+    Behavior:
+      - Reads JSON body
+      - Forces stream=true
+      - Proxies to upstream POST /v1/responses
+      - Passes upstream SSE through verbatim (no reformatting)
+    """
+    try:
+        payload: Dict[str, Any] = {}
+        raw = await request.body()
+        if raw:
+            payload = json.loads(raw.decode("utf-8"))
+
+        payload["stream"] = True
+
+        upstream_url = _join_upstream_url(settings.OPENAI_API_BASE, "/v1/responses", "")
+        headers = _build_outbound_headers(request.headers.items())
+        headers["Accept"] = "text/event-stream"
+        headers["Content-Type"] = "application/json"
+
+        client = get_async_httpx_client(timeout=float(settings.PROXY_TIMEOUT_SECONDS))
+        req = client.build_request("POST", upstream_url, headers=headers, json=payload)
+        resp = await client.send(req, stream=True)
+
+        content_type = resp.headers.get("content-type", "text/event-stream")
+        filtered_headers = _filter_response_headers(resp.headers)
+
+        if not content_type.lower().startswith("text/event-stream"):
+            data = await resp.aread()
+            await resp.aclose()
+            return Response(
+                content=data,
+                status_code=resp.status_code,
+                headers=filtered_headers,
+                media_type=content_type,
+            )
+
+        logger.info("↔ upstream SSE POST /v1/responses (via /v1/responses:stream)")
+
+        async def _aiter():
+            async for chunk in resp.aiter_bytes():
+                yield chunk
+            await resp.aclose()
+
+        return StreamingResponse(
+            _aiter(),
+            status_code=resp.status_code,
+            headers=filtered_headers,
+            media_type=content_type,
+        )
+
+    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
+        return JSONResponse(status_code=400, content={"detail": "Invalid JSON body", "error": str(exc)})
+    except httpx.HTTPError as exc:
+        return JSONResponse(status_code=424, content={"detail": "Upstream request failed", "error": str(exc)})
+    except Exception as exc:
+        return JSONResponse(status_code=424, content={"detail": "Relay wiring error", "error": str(exc)})
diff --git a/app/api/tools_api.py b/app/api/tools_api.py
index 86190d6..7537d2f 100755
--- a/app/api/tools_api.py
+++ b/app/api/tools_api.py
@@ -1,8 +1,8 @@
+# app/api/tools_api.py
 from __future__ import annotations
 
-import json
-from pathlib import Path
-from typing import Any, Dict, List, Set
+import copy
+from typing import Any, Dict
 
 from fastapi import APIRouter, Request
 from fastapi.responses import JSONResponse
@@ -12,37 +12,11 @@ from app.core.config import get_settings
 router = APIRouter()
 
 
-def _load_tools_manifest() -> List[Dict[str, Any]]:
-    """
-    Optional helper: if app/manifests/tools_manifest.json exists, include it in /manifest.
-    """
-    app_dir = Path(__file__).resolve().parents[1]
-    candidates = [
-        app_dir / "manifests" / "tools_manifest.json",
-        app_dir / "manifests" / "tools_manifest.tools.json",
-    ]
-    for p in candidates:
-        if p.exists() and p.is_file():
-            try:
-                with p.open("r", encoding="utf-8") as f:
-                    data = json.load(f)
-                return data if isinstance(data, list) else []
-            except Exception:
-                return []
-    return []
-
-
-def _manifest_endpoints() -> Dict[str, List[str]]:
-    """
-    Canonical manifest endpoint groups.
+def _build_manifest() -> Dict[str, Any]:
+    s = get_settings()
 
-    Baseline tests require:
-      - data.endpoints.responses includes /v1/responses
-      - data.endpoints.responses_compact includes /v1/responses/compact
-    """
-    return {
+    endpoints = {
         "health": ["/health", "/v1/health"],
-        "actions": ["/v1/actions/ping", "/v1/actions/health", "/v1/actions/schema"],
         "models": ["/v1/models", "/v1/models/{model}"],
         "responses": [
             "/v1/responses",
@@ -52,16 +26,9 @@ def _manifest_endpoints() -> Dict[str, List[str]]:
         ],
         "responses_compact": ["/v1/responses/compact"],
         "embeddings": ["/v1/embeddings"],
-        "images": [
-            "/v1/images/generations",
-            "/v1/images",
-            "/v1/images/edits",
-            "/v1/images/variations",
-        ],
-        "images_actions": [
-            "/v1/actions/images/edits",
-            "/v1/actions/images/variations",
-        ],
+        "images": ["/v1/images/generations", "/v1/images/edits", "/v1/images/variations"],
+        "images_actions": ["/v1/actions/images/edits", "/v1/actions/images/variations"],
+        "files": ["/v1/files", "/v1/files/{file_id}", "/v1/files/{file_id}/content"],
         "uploads": [
             "/v1/uploads",
             "/v1/uploads/{upload_id}",
@@ -69,101 +36,69 @@ def _manifest_endpoints() -> Dict[str, List[str]]:
             "/v1/uploads/{upload_id}/complete",
             "/v1/uploads/{upload_id}/cancel",
         ],
-        "files": [
-            "/v1/files",
-            "/v1/files/{file_id}",
-            "/v1/files/{file_id}/content",
-        ],
-        "batches": [
-            "/v1/batches",
-            "/v1/batches/{batch_id}",
-            "/v1/batches/{batch_id}/cancel",
-        ],
-        "realtime": ["/v1/realtime/sessions"],
-        "conversations": ["/v1/conversations", "/v1/conversations/{path}"],
-        "vector_stores": ["/v1/vector_stores", "/v1/vector_stores/{path}"],
+        "batches": ["/v1/batches", "/v1/batches/{batch_id}", "/v1/batches/{batch_id}/cancel"],
         "proxy": ["/v1/proxy"],
+        "realtime_http": ["/v1/realtime/sessions"],
+        "realtime_ws": ["/v1/realtime/ws"],
     }
 
-
-def build_manifest_response(base_url: str = "") -> Dict[str, Any]:
-    settings = get_settings()
-
-    manifest = {
-        "name": settings.RELAY_NAME,
-        "version": "1.0.0",
-        "description": "OpenAI-compatible relay with explicit subroutes and Actions-friendly wrappers.",
-        "tools": _load_tools_manifest(),
-        "endpoints": _manifest_endpoints(),
-        "meta": {
-            "app_mode": settings.APP_MODE,
-            "environment": settings.ENVIRONMENT,
-            "relay_auth_enabled": bool(settings.RELAY_AUTH_ENABLED),
-            "relay_auth_header": settings.RELAY_AUTH_HEADER,
-            "upstream_base_url": settings.UPSTREAM_BASE_URL,
-            "openapi_url": "/openapi.json",
-            "actions_openapi_url": "/openapi.actions.json",
-        },
+    meta = {
+        "relay_name": getattr(s, "RELAY_NAME", "chatgpt-team-relay"),
+        "auth_required": bool(getattr(s, "RELAY_AUTH_ENABLED", False)),
+        "auth_header": "X-Relay-Key",
+        "upstream_base_url": getattr(s, "UPSTREAM_BASE_URL", getattr(s, "OPENAI_API_BASE", "")),
+        "actions_openapi_url": "/openapi.actions.json",
+        "actions_openapi_groups": [
+            "health",
+            "models",
+            "responses",
+            "responses_compact",
+            "embeddings",
+            "images",
+            "images_actions",
+            "proxy",
+            "realtime_http",
+        ],
     }
 
+    # Provide both "old" and "new" shapes for compatibility:
     return {
         "object": "relay.manifest",
-        "data": manifest,
-        "meta": {"base_url": base_url},
+        "data": {"endpoints": endpoints, "meta": meta},
+        "endpoints": endpoints,
+        "meta": meta,
     }
 
 
 @router.get("/manifest", include_in_schema=False)
-async def manifest(request: Request) -> JSONResponse:
-    base_url = str(request.base_url).rstrip("/")
-    return JSONResponse(content=build_manifest_response(base_url=base_url))
-
-
 @router.get("/v1/manifest", include_in_schema=False)
-async def manifest_v1(request: Request) -> JSONResponse:
-    base_url = str(request.base_url).rstrip("/")
-    return JSONResponse(content=build_manifest_response(base_url=base_url))
+async def get_manifest() -> Dict[str, Any]:
+    return _build_manifest()
 
 
-def _collect_allowed_paths(manifest: Dict[str, Any]) -> Set[str]:
-    allowed: Set[str] = set()
-    endpoints = manifest.get("endpoints") or {}
-    if isinstance(endpoints, dict):
-        for paths in endpoints.values():
-            if isinstance(paths, list):
-                for p in paths:
-                    if not isinstance(p, str):
-                        continue
-                    # Normalize placeholder used by some wildcard routes
-                    allowed.add(p.replace("{path}", "{path:path}"))
-    return allowed
-
-
-def _filtered_openapi_for_actions(request: Request) -> Dict[str, Any]:
+@router.get("/openapi.actions.json", include_in_schema=False)
+async def openapi_actions(request: Request) -> JSONResponse:
     """
-    Actions-focused OpenAPI document by filtering app.openapi()
-    down to the paths we advertise in /manifest.
+    Curated OpenAPI subset for ChatGPT Actions (REST; no WebSocket client).
     """
-    base = request.app.openapi()
-    manifest = build_manifest_response(base_url=str(request.base_url).rstrip("/"))["data"]
-    allowed = _collect_allowed_paths(manifest)
-
-    base_paths = base.get("paths") or {}
-    base["paths"] = {k: v for k, v in base_paths.items() if k in allowed}
+    full = request.app.openapi()
+    manifest = _build_manifest()
 
-    info = base.get("info") or {}
-    title = info.get("title") or "OpenAI Relay"
-    info["title"] = f"{title} (Actions)"
-    base["info"] = info
+    groups = (manifest.get("meta") or {}).get("actions_openapi_groups") or []
+    endpoints = manifest.get("endpoints") or {}
+    allowed_paths: set[str] = set()
 
-    return base
+    for g in groups:
+        allowed_paths.update(endpoints.get(str(g), []) or [])
 
+    allowed_paths.update({"/health", "/v1/health"})
 
-@router.get("/openapi.actions.json", include_in_schema=False)
-async def openapi_actions_json(request: Request) -> JSONResponse:
-    return JSONResponse(content=_filtered_openapi_for_actions(request))
+    filtered = copy.deepcopy(full)
+    filtered["paths"] = {p: spec for p, spec in (full.get("paths") or {}).items() if p in allowed_paths}
 
+    info = filtered.get("info") or {}
+    title = str(info.get("title") or "OpenAPI")
+    info["title"] = f"{title} (Actions subset)"
+    filtered["info"] = info
 
-@router.get("/v1/openapi.actions.json", include_in_schema=False)
-async def openapi_actions_json_v1(request: Request) -> JSONResponse:
-    return JSONResponse(content=_filtered_openapi_for_actions(request))
+    return JSONResponse(filtered)
diff --git a/app/core/config.py b/app/core/config.py
index da57b41..416e8da 100755
--- a/app/core/config.py
+++ b/app/core/config.py
@@ -22,19 +22,21 @@ def _bool_env(key: str, default: bool = False) -> bool:
 
 def _csv_env(key: str, default: Optional[List[str]] = None) -> List[str]:
     val = os.getenv(key)
-    if not val:
-        return list(default or [])
-    return [x.strip() for x in val.split(",") if x.strip()]
+    if val is None:
+        return [] if default is None else default
+    parts = [p.strip() for p in val.split(",")]
+    return [p for p in parts if p]
 
 
 def _normalize_url(url: str) -> str:
-    return (url or "").strip().rstrip("/")
+    url = (url or "").strip()
+    return url.rstrip("/") if url else ""
 
 
 def _strip_v1(url: str) -> str:
     url = _normalize_url(url)
     if url.endswith("/v1"):
-        return url[:-3].rstrip("/")
+        return url[: -len("/v1")]
     return url
 
 
@@ -99,22 +101,12 @@ class Settings:
         if not self.openai_base_url:
             raise ValueError("openai_base_url must not be empty")
         if self.relay_auth_enabled and not self.relay_key:
-            raise ValueError("RELAY_AUTH_ENABLED=true requires RELAY_KEY")
-
-    def upstream_headers(self) -> dict:
-        headers = {"Authorization": f"Bearer {self.openai_api_key}"}
-        if self.openai_organization:
-            headers["OpenAI-Organization"] = self.openai_organization
-        if self.openai_project:
-            headers["OpenAI-Project"] = self.openai_project
-        if self.openai_beta:
-            headers["OpenAI-Beta"] = self.openai_beta
-        return headers
-
-    # ---------------------------------------------------------------------
-    # Uppercase aliases (compat with older code / tests).
-    # Include setters so tests can monkeypatch them.
-    # ---------------------------------------------------------------------
+            raise ValueError("RELAY_AUTH_ENABLED=true requires RELAY_KEY to be set")
+
+    # -------------------------------------------------------------------------
+    # Legacy / compatibility aliases (upper-case properties)
+    # -------------------------------------------------------------------------
+
     @property
     def APP_MODE(self) -> str:
         return self.app_mode
@@ -166,6 +158,41 @@ class Settings:
         self.openai_base_url = base or "https://api.openai.com"
         self.openai_api_base = f"{self.openai_base_url}/v1"
 
+    @property
+    def OPENAI_BASE_URL(self) -> str:
+        """Legacy/compat alias for `openai_base_url` (no `/v1`)."""
+        return self.openai_base_url
+
+    @OPENAI_BASE_URL.setter
+    def OPENAI_BASE_URL(self, value: str) -> None:
+        base = _normalize_url(value)
+        self.openai_base_url = base or "https://api.openai.com"
+        self.openai_api_base = f"{self.openai_base_url}/v1"
+
+    @property
+    def OPENAI_ORG(self) -> str:
+        return self.openai_organization
+
+    @OPENAI_ORG.setter
+    def OPENAI_ORG(self, value: str) -> None:
+        self.openai_organization = value or ""
+
+    @property
+    def OPENAI_ORGANIZATION(self) -> str:
+        return self.openai_organization
+
+    @OPENAI_ORGANIZATION.setter
+    def OPENAI_ORGANIZATION(self, value: str) -> None:
+        self.openai_organization = value or ""
+
+    @property
+    def OPENAI_PROJECT(self) -> str:
+        return self.openai_project
+
+    @OPENAI_PROJECT.setter
+    def OPENAI_PROJECT(self, value: str) -> None:
+        self.openai_project = value or ""
+
     @property
     def UPSTREAM_BASE_URL(self) -> str:
         return self.openai_base_url
@@ -208,6 +235,63 @@ class Settings:
     def RELAY_TIMEOUT_SECONDS(self, value: float) -> None:
         self.relay_timeout_seconds = float(value)
 
+    @property
+    def PROXY_TIMEOUT_SECONDS(self) -> float:
+        """Compat alias used by some proxy/SSE routes."""
+        return self.relay_timeout_seconds
+
+    @PROXY_TIMEOUT_SECONDS.setter
+    def PROXY_TIMEOUT_SECONDS(self, value: float) -> None:
+        self.relay_timeout_seconds = float(value)
+
+    @property
+    def PROXY_TIMEOUT(self) -> float:
+        return self.relay_timeout_seconds
+
+    @PROXY_TIMEOUT.setter
+    def PROXY_TIMEOUT(self, value: float) -> None:
+        self.relay_timeout_seconds = float(value)
+
+    @property
+    def PROXY_TIMEOUT_S(self) -> float:
+        return self.relay_timeout_seconds
+
+    @PROXY_TIMEOUT_S.setter
+    def PROXY_TIMEOUT_S(self, value: float) -> None:
+        self.relay_timeout_seconds = float(value)
+
+    @property
+    def RELAY_TIMEOUT(self) -> float:
+        return self.relay_timeout_seconds
+
+    @RELAY_TIMEOUT.setter
+    def RELAY_TIMEOUT(self, value: float) -> None:
+        self.relay_timeout_seconds = float(value)
+
+    @property
+    def RELAY_TIMEOUT_S(self) -> float:
+        return self.relay_timeout_seconds
+
+    @RELAY_TIMEOUT_S.setter
+    def RELAY_TIMEOUT_S(self, value: float) -> None:
+        self.relay_timeout_seconds = float(value)
+
+    @property
+    def OPENAI_TIMEOUT(self) -> float:
+        return self.relay_timeout_seconds
+
+    @OPENAI_TIMEOUT.setter
+    def OPENAI_TIMEOUT(self, value: float) -> None:
+        self.relay_timeout_seconds = float(value)
+
+    @property
+    def OPENAI_TIMEOUT_S(self) -> float:
+        return self.relay_timeout_seconds
+
+    @OPENAI_TIMEOUT_S.setter
+    def OPENAI_TIMEOUT_S(self, value: float) -> None:
+        self.relay_timeout_seconds = float(value)
+
     @property
     def DEFAULT_MODEL(self) -> str:
         return self.default_model
@@ -264,7 +348,7 @@ class Settings:
     def ENVIRONMENT(self, value: str) -> None:
         self.environment = value or self.environment
 
-    # Back-compat: some older code referenced this attribute name.
+    # Lowercase compat alias used by some older code
     @property
     def proxy_timeout_seconds(self) -> float:
         return self.relay_timeout_seconds
@@ -285,8 +369,8 @@ def get_settings() -> Settings:
     return _settings_cache
 
 
-# Convenience singleton (tests may monkeypatch attributes on this instance)
+# Singleton (tests may monkeypatch attributes on this instance)
 settings = get_settings()
 
-# Local logger for modules that import it from here.
-logger = logging.getLogger("relay")
+
+__all__ = ["Settings", "get_settings", "settings"]
diff --git a/app/core/http_client.py b/app/core/http_client.py
index 317053e..aca6729 100644
--- a/app/core/http_client.py
+++ b/app/core/http_client.py
@@ -1,167 +1,152 @@
 from __future__ import annotations
 
 import asyncio
-import contextvars
-from typing import Optional, Tuple, Any, Callable
+import os
+from typing import Dict, Optional, Tuple
 
 import httpx
 from openai import AsyncOpenAI
 
-from app.core.config import settings
+from app.core.config import get_settings
 
-_httpx_client_var: contextvars.ContextVar[
-    Optional[Tuple[asyncio.AbstractEventLoop, httpx.AsyncClient]]
-] = contextvars.ContextVar("httpx_async_client", default=None)
+# Cache clients per-event-loop and timeout to avoid cross-loop reuse issues.
+# Key: (id(loop), timeout_seconds)
+_LOOP_CLIENTS: Dict[Tuple[int, float], Tuple[httpx.AsyncClient, AsyncOpenAI]] = {}
 
-_openai_client_var: contextvars.ContextVar[
-    Optional[Tuple[asyncio.AbstractEventLoop, AsyncOpenAI]]
-] = contextvars.ContextVar("openai_async_client", default=None)
 
+def _get_or_set_loop() -> asyncio.AbstractEventLoop:
+    """
+    Returns the running loop if available. If called from a sync context (e.g. python -c),
+    creates and sets a new event loop so client construction remains usable.
+    """
+    try:
+        return asyncio.get_running_loop()
+    except RuntimeError:
+        loop = asyncio.new_event_loop()
+        asyncio.set_event_loop(loop)
+        return loop
 
-def _get_setting(*names: str, default=None):
-    for name in names:
-        if hasattr(settings, name):
-            val = getattr(settings, name)
-            if val is not None:
-                return val
-    return default
 
+def _resolve_openai_api_base(settings: object) -> str:
+    """
+    Resolve the upstream OpenAI API base.
 
-def _default_timeout_s() -> float:
-    # Support multiple historical config names.
-    return float(
-        _get_setting(
-            "RELAY_TIMEOUT",
-            "RELAY_TIMEOUT_S",
-            "OPENAI_TIMEOUT",
-            "OPENAI_TIMEOUT_S",
-            default=60.0,
-        )
+    IMPORTANT: Prefer OPENAI_API_BASE / settings.openai_api_base over OPENAI_BASE_URL to avoid
+    accidentally pointing back to the relay itself.
+    """
+    candidate = (
+        getattr(settings, "openai_api_base", None)
+        or os.getenv("OPENAI_API_BASE")
+        or os.getenv("OPENAI_API_BASE_URL")
     )
+    if not candidate:
+        candidate = "https://api.openai.com/v1"
+    return str(candidate).rstrip("/")
 
 
-def get_async_httpx_client(timeout: Optional[float] = None) -> httpx.AsyncClient:
-    """
-    Canonical shared AsyncClient (per event loop).
+def _resolve_openai_api_key(settings: object) -> Optional[str]:
+    return getattr(settings, "openai_api_key", None) or os.getenv("OPENAI_API_KEY")
 
-    This is the single HTTP connection pool used for all upstream calls.
-    """
-    loop = asyncio.get_running_loop()
-    cached = _httpx_client_var.get()
-    if cached and cached[0] is loop:
-        return cached[1]
 
-    t = float(timeout) if timeout is not None else _default_timeout_s()
+def _resolve_timeout_seconds(settings: object, timeout: Optional[float]) -> float:
+    if timeout is not None:
+        return float(timeout)
 
-    client = httpx.AsyncClient(
-        timeout=httpx.Timeout(t),
-        limits=httpx.Limits(max_connections=200, max_keepalive_connections=50),
-        follow_redirects=True,
-    )
-    _httpx_client_var.set((loop, client))
-    return client
+    # Try common project-level settings fields first (kept flexible for refactors).
+    for attr in ("proxy_timeout_seconds", "relay_timeout_seconds", "openai_timeout_seconds"):
+        val = getattr(settings, attr, None)
+        if val is not None:
+            return float(val)
 
+    # Environment fallback
+    env_val = os.getenv("RELAY_TIMEOUT_SECONDS")
+    if env_val:
+        try:
+            return float(env_val)
+        except ValueError:
+            pass
 
-def get_async_openai_client() -> AsyncOpenAI:
-    """
-    Canonical shared AsyncOpenAI client (per event loop).
+    # Safe default
+    return 60.0
 
-    Uses the canonical HTTPX pool from get_async_httpx_client().
-    """
-    loop = asyncio.get_running_loop()
-    cached = _openai_client_var.get()
-    if cached and cached[0] is loop:
-        return cached[1]
-
-    api_key = _get_setting("OPENAI_API_KEY", "openai_api_key")
-    if not api_key:
-        raise RuntimeError("OPENAI_API_KEY is not configured.")
-
-    base_url = _get_setting(
-        "OPENAI_BASE_URL",
-        "OPENAI_API_BASE",
-        "openai_base_url",
-        "openai_api_base",
-        default="https://api.openai.com/v1",
-    )
 
-    organization = _get_setting("OPENAI_ORG", "OPENAI_ORGANIZATION", "openai_organization")
-    project = _get_setting("OPENAI_PROJECT", "openai_project")
+def _get_or_create_clients(timeout_seconds: float) -> Tuple[httpx.AsyncClient, AsyncOpenAI]:
+    loop = _get_or_set_loop()
+    cache_key = (id(loop), float(timeout_seconds))
+
+    existing = _LOOP_CLIENTS.get(cache_key)
+    if existing is not None:
+        return existing
+
+    settings = get_settings()
+    base_url = _resolve_openai_api_base(settings)
+    api_key = _resolve_openai_api_key(settings)
 
-    # Reuse our HTTPX pool for upstream calls.
-    http_client = get_async_httpx_client()
+    headers = {"User-Agent": "chatgpt-team-relay/1.0"}
+    if api_key:
+        headers["Authorization"] = f"Bearer {api_key}"
 
-    client = AsyncOpenAI(
-        api_key=api_key,
+    httpx_client = httpx.AsyncClient(
         base_url=base_url,
-        organization=organization,
-        project=project,
-        http_client=http_client,
+        timeout=float(timeout_seconds),
+        headers=headers,
     )
 
-    _openai_client_var.set((loop, client))
-    return client
+    openai_kwargs = {"base_url": base_url, "http_client": httpx_client}
+    if api_key:
+        openai_kwargs["api_key"] = api_key
 
+    openai_client = AsyncOpenAI(**openai_kwargs)
 
-async def _maybe_close(obj: Any) -> None:
+    _LOOP_CLIENTS[cache_key] = (httpx_client, openai_client)
+    return httpx_client, openai_client
+
+
+def get_async_httpx_client(timeout: Optional[float] = None) -> httpx.AsyncClient:
     """
-    Best-effort close for objects that may expose:
-      - aclose() (async)
-      - close() (sync or async)
+    Shared AsyncClient for upstream OpenAI HTTP calls (used by forward/proxy routes).
     """
-    if obj is None:
-        return
+    settings = get_settings()
+    effective_timeout = _resolve_timeout_seconds(settings, timeout)
+    httpx_client, _ = _get_or_create_clients(effective_timeout)
+    return httpx_client
 
-    closer: Optional[Callable[[], Any]] = None
-    if hasattr(obj, "aclose") and callable(getattr(obj, "aclose")):
-        closer = getattr(obj, "aclose")
-    elif hasattr(obj, "close") and callable(getattr(obj, "close")):
-        closer = getattr(obj, "close")
 
-    if closer is None:
-        return
-
-    try:
-        res = closer()
-        if asyncio.iscoroutine(res):
-            await res
-    except Exception:
-        # Shutdown should be best-effort; avoid masking the real shutdown path.
-        return
+def get_async_openai_client(timeout: Optional[float] = None) -> AsyncOpenAI:
+    """
+    Shared AsyncOpenAI client (SDK-backed calls).
+    """
+    settings = get_settings()
+    effective_timeout = _resolve_timeout_seconds(settings, timeout)
+    _, openai_client = _get_or_create_clients(effective_timeout)
+    return openai_client
 
 
 async def close_async_clients() -> None:
     """
-    FastAPI shutdown hook.
-
-    Closes cached per-event-loop clients created by:
-      - get_async_httpx_client()
-      - get_async_openai_client()
-
-    Safe to call multiple times.
+    Close cached clients for the *current* event loop.
     """
     try:
         loop = asyncio.get_running_loop()
     except RuntimeError:
-        # No running loop: nothing to close safely in this context.
+        # No running loop; close everything to avoid leaks in CLI contexts.
+        await aclose_all_clients()
         return
 
-    cached_openai = _openai_client_var.get()
-    cached_httpx = _httpx_client_var.get()
+    loop_id = id(loop)
+    keys_to_close = [k for k in _LOOP_CLIENTS.keys() if k[0] == loop_id]
 
-    # Close OpenAI client first (it references the HTTP client).
-    if cached_openai and cached_openai[0] is loop:
-        await _maybe_close(cached_openai[1])
-        _openai_client_var.set(None)
+    for key in keys_to_close:
+        httpx_client, _ = _LOOP_CLIENTS.pop(key)
+        await httpx_client.aclose()
 
-    # Close HTTPX pool.
-    if cached_httpx and cached_httpx[0] is loop:
-        await _maybe_close(cached_httpx[1])
-        _httpx_client_var.set(None)
 
+async def aclose_all_clients() -> None:
+    """
+    Close all cached clients across all loops (primarily for tests / shutdown hooks).
+    """
+    items = list(_LOOP_CLIENTS.items())
+    _LOOP_CLIENTS.clear()
 
-__all__ = [
-    "get_async_httpx_client",
-    "get_async_openai_client",
-    "close_async_clients",
-]
+    for _, (httpx_client, _) in items:
+        await httpx_client.aclose()
diff --git a/app/http_client.py b/app/http_client.py
index da4a4a6..4071691 100644
--- a/app/http_client.py
+++ b/app/http_client.py
@@ -1,10 +1,24 @@
+"""
+Compatibility shim for legacy imports.
+
+Some modules historically imported client helpers from `app.http_client`.
+The canonical implementations live in `app.core.http_client`.
+
+This module re-exports the public helpers to avoid churn and circular edits.
+"""
+
 from __future__ import annotations
 
-# Keep legacy imports working without duplicating logic.
-from app.core.http_client import (
+from app.core.http_client import (  # noqa: F401
+    aclose_all_clients,
+    close_async_clients,
     get_async_httpx_client,
     get_async_openai_client,
-    close_async_clients,
 )
 
-__all__ = ["get_async_httpx_client", "get_async_openai_client", "close_async_clients"]
+__all__ = [
+    "get_async_httpx_client",
+    "get_async_openai_client",
+    "close_async_clients",
+    "aclose_all_clients",
+]
diff --git a/app/main.py b/app/main.py
index 18fa9a2..adeba31 100755
--- a/app/main.py
+++ b/app/main.py
@@ -1,56 +1,45 @@
 from __future__ import annotations
 
-import logging
-
-from fastapi import FastAPI, Request
+from fastapi import FastAPI
 from fastapi.middleware.cors import CORSMiddleware
 
+from app.api.routes import router as api_router
 from app.api.sse import router as sse_router
 from app.api.tools_api import router as tools_router
 from app.core.config import get_settings
+from app.middleware.p4_orchestrator import P4OrchestratorMiddleware
 from app.middleware.relay_auth import RelayAuthMiddleware
-from app.routes.register_routes import register_routes
-
-logger = logging.getLogger("relay")
+from app.middleware.validation import ValidationMiddleware
 
 
 def create_app() -> FastAPI:
     settings = get_settings()
 
     app = FastAPI(
-        title="OpenAI-compatible Relay",
-        version="1.0.0",
-        docs_url=None,
-        redoc_url=None,
-        openapi_url="/openapi.json",
+        title=getattr(settings, "RELAY_NAME", "ChatGPT Team Relay"),
+        version="0.0.0",
     )
 
     app.add_middleware(
         CORSMiddleware,
-        allow_origins=settings.CORS_ALLOW_ORIGINS,
-        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
-        allow_methods=settings.CORS_ALLOW_METHODS,
-        allow_headers=settings.CORS_ALLOW_HEADERS,
+        allow_origins=settings.cors_allow_origins,
+        allow_credentials=settings.cors_allow_credentials,
+        allow_methods=settings.cors_allow_methods,
+        allow_headers=settings.cors_allow_headers,
     )
 
+    # Middlewares (order: last added runs first)
+    app.add_middleware(P4OrchestratorMiddleware)
+
+    # Always install RelayAuthMiddleware; it no-ops when RELAY_AUTH_ENABLED is false.
     app.add_middleware(RelayAuthMiddleware)
 
-    register_routes(app)
-    app.include_router(tools_router)
-    app.include_router(sse_router)
+    app.add_middleware(ValidationMiddleware)
 
-    @app.middleware("http")
-    async def _log_requests(request: Request, call_next):
-        response = await call_next(request)
-        try:
-            logger.info("%s %s -> %s", request.method, request.url.path, response.status_code)
-        except Exception:
-            pass
-        return response
-
-    @app.get("/", include_in_schema=False)
-    async def root():
-        return {"status": "ok", "service": "openai-relay"}
+    # Routers
+    app.include_router(sse_router)
+    app.include_router(tools_router)
+    app.include_router(api_router)
 
     return app
 
diff --git a/app/middleware/relay_auth.py b/app/middleware/relay_auth.py
index 2295ef7..61190a9 100755
--- a/app/middleware/relay_auth.py
+++ b/app/middleware/relay_auth.py
@@ -1,40 +1,52 @@
 from __future__ import annotations
 
-from typing import Callable
+from typing import Optional
 
-from fastapi import Request
-from starlette.middleware.base import BaseHTTPMiddleware
-from starlette.responses import Response
+from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
+from starlette.requests import Request
+from starlette.responses import JSONResponse, Response
 
-from app.utils.authy import check_relay_key
+from app.core.config import settings
+
+
+_PUBLIC_PATHS = {
+    "/health",
+    "/v1/health",
+    "/manifest",
+    "/openapi.json",
+    "/openapi.actions.json",
+}
+
+
+def _extract_relay_key(request: Request) -> Optional[str]:
+    # Preferred header
+    x_key = request.headers.get("X-Relay-Key")
+    if x_key:
+        return x_key.strip()
+
+    # Bearer fallback
+    auth = request.headers.get("Authorization") or ""
+    auth = auth.strip()
+    if auth.lower().startswith("bearer "):
+        return auth[7:].strip()
+
+    return None
 
 
 class RelayAuthMiddleware(BaseHTTPMiddleware):
-    """
-    Enforces an internal "relay key" (client -> relay) for /v1/* endpoints when enabled.
-    """
-
-    _PUBLIC_PATHS = {
-        "/",
-        "/health",
-        "/v1/health",
-        "/manifest",
-        "/v1/manifest",
-        "/openapi.json",
-        "/openapi.actions.json",
-        "/v1/openapi.actions.json",
-        "/docs",
-        "/redoc",
-        "/favicon.ico",
-    }
-
-    async def dispatch(self, request: Request, call_next: Callable[[Request], Response]) -> Response:
-        path = request.url.path
-
-        if path in self._PUBLIC_PATHS or path.startswith("/static"):
+    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
+        # Allow unauthenticated access to public endpoints (health/openapi/manifest).
+        if request.url.path in _PUBLIC_PATHS or request.url.path.startswith("/static/"):
+            return await call_next(request)
+
+        if not settings.RELAY_AUTH_ENABLED:
             return await call_next(request)
 
-        if path.startswith("/v1"):
-            check_relay_key(request)
+        provided = _extract_relay_key(request)
+        if not provided:
+            return JSONResponse(status_code=401, content={"detail": "Missing relay key"})
+
+        if provided != settings.RELAY_KEY:
+            return JSONResponse(status_code=401, content={"detail": "Invalid relay key"})
 
         return await call_next(request)
diff --git a/app/routes/images.py b/app/routes/images.py
index 5b3cff5..31e5b8b 100755
--- a/app/routes/images.py
+++ b/app/routes/images.py
@@ -1,308 +1,348 @@
+# app/api/images.py
 from __future__ import annotations
 
 import base64
-import binascii
-import ipaddress
-from typing import Any, Optional
+import json
+from typing import Any, Dict, List, Mapping, Optional, Tuple
 from urllib.parse import urlparse
 
 import httpx
-from fastapi import APIRouter, Request
-from fastapi.responses import JSONResponse
+from fastapi import APIRouter, HTTPException, Request
 from pydantic import BaseModel, Field
 from starlette.responses import Response
 
-from app.api.forward_openai import (
-    build_outbound_headers,
-    build_upstream_url,
-    filter_upstream_headers,
-    forward_openai_request,
-)
+from app.api.forward_openai import forward_openai_request
 from app.core.config import get_settings
-from app.core.http_client import get_async_httpx_client
-from app.models.error import ErrorResponse
 from app.utils.logger import relay_log as logger
 
 router = APIRouter(prefix="/v1", tags=["images"])
+actions_router = APIRouter(prefix="/v1/actions/images", tags=["images_actions"])
+
+# SSRF hardening: allow only OpenAI-controlled download hosts.
+_ALLOWED_HOSTS_EXACT: set[str] = {
+    "files.openai.com",
+}
+_ALLOWED_HOST_SUFFIXES: Tuple[str, ...] = (
+    "oaiusercontent.com",
+    "openai.com",
+    "openaiusercontent.com",
+)
+_ALLOWED_AZURE_BLOBS_PREFIXES: Tuple[str, ...] = (
+    "oaidalle",
+    "oaidalleapiprod",
+)
 
-_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
-_MAX_PNG_BYTES = 4 * 1024 * 1024  # 4 MiB (matches upstream constraint)
+_MAX_IMAGE_BYTES = 4 * 1024 * 1024  # 4MB
+_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
 
 
-# ---------------------------------------------------------------------------
-# Direct OpenAI-compatible endpoints (multipart)
-# ---------------------------------------------------------------------------
+class OpenAIFileIdRef(BaseModel):
+    id: Optional[str] = None
+    name: Optional[str] = None
+    mime_type: Optional[str] = Field(default=None, alias="mime_type")
+    download_link: Optional[str] = None
 
-@router.post("/images", summary="Create image generation")
-@router.post("/images/generations", summary="Create image generation (alias)")
-async def create_image(request: Request) -> Response:
-    logger.info("→ [images] %s %s", request.method, request.url.path)
-    return await forward_openai_request(request)
 
+class ImagesVariationsJSON(BaseModel):
+    # Primary Actions file input
+    openaiFileIdRefs: Optional[List[OpenAIFileIdRef]] = None
 
-@router.post("/images/edits", summary="Edit an image (multipart)")
-async def edit_image(request: Request) -> Response:
-    logger.info("→ [images] %s %s (edits)", request.method, request.url.path)
-    return await forward_openai_request(request)
+    # Fallbacks
+    image_url: Optional[str] = None
+    image_base64: Optional[str] = None
 
+    # Standard params
+    model: Optional[str] = None
+    n: Optional[int] = None
+    size: Optional[str] = None
+    response_format: Optional[str] = None
+    user: Optional[str] = None
 
-@router.post("/images/variations", summary="Create image variations (multipart)")
-async def variations_image(request: Request) -> Response:
-    logger.info("→ [images] %s %s (variations)", request.method, request.url.path)
-    return await forward_openai_request(request)
 
+class ImagesEditsJSON(BaseModel):
+    openaiFileIdRefs: Optional[List[OpenAIFileIdRef]] = None
 
-# ---------------------------------------------------------------------------
-# Actions-friendly wrappers (JSON body with file URLs/base64)
-# ---------------------------------------------------------------------------
-
-class ActionImageVariationsRequest(BaseModel):
-    image_url: Optional[str] = Field(
-        default=None,
-        description="HTTPS URL to a PNG image (ChatGPT Actions file_url mode).",
-    )
-    image_base64: Optional[str] = Field(
-        default=None,
-        description="Base64-encoded PNG bytes (optionally a data: URL).",
-    )
-    model: Optional[str] = Field(default=None, description="Optional upstream model parameter (if supported).")
-    n: Optional[int] = Field(default=1, ge=1, le=10)
-    size: Optional[str] = Field(default=None, description="e.g. 256x256, 512x512, 1024x1024")
-    response_format: Optional[str] = Field(default=None, description="url or b64_json")
-    user: Optional[str] = Field(default=None)
-
-
-class ActionImageEditsRequest(BaseModel):
-    prompt: str = Field(..., min_length=1)
-    image_url: Optional[str] = Field(default=None, description="HTTPS URL to a PNG image.")
-    image_base64: Optional[str] = Field(default=None, description="Base64-encoded PNG bytes (optionally a data: URL).")
-    mask_url: Optional[str] = Field(default=None, description="HTTPS URL to a PNG mask image.")
-    mask_base64: Optional[str] = Field(default=None, description="Base64-encoded PNG mask bytes (optionally a data: URL).")
-    model: Optional[str] = Field(default=None, description="Optional upstream model parameter (if supported).")
-    n: Optional[int] = Field(default=1, ge=1, le=10)
-    size: Optional[str] = Field(default=None, description="e.g. 256x256, 512x512, 1024x1024")
-    response_format: Optional[str] = Field(default=None, description="url or b64_json")
-    user: Optional[str] = Field(default=None)
-
-
-def _error(status_code: int, message: str, code: str | None = None, param: str | None = None) -> JSONResponse:
-    payload = ErrorResponse(
-        error={
-            "message": message,
-            "type": "invalid_request_error",
-            "param": param,
-            "code": code,
-        }
-    )
-    return JSONResponse(status_code=status_code, content=payload.model_dump())
+    image_url: Optional[str] = None
+    image_base64: Optional[str] = None
+    mask_url: Optional[str] = None
+    mask_base64: Optional[str] = None
 
+    prompt: Optional[str] = None
+    model: Optional[str] = None
+    n: Optional[int] = None
+    size: Optional[str] = None
+    response_format: Optional[str] = None
+    user: Optional[str] = None
 
-def _strip_data_url_prefix(b64: str) -> str:
-    # Accept: data:image/png;base64,XXXX
-    prefix = "data:image/png;base64,"
-    if b64.startswith(prefix):
-        return b64[len(prefix) :]
-    return b64
 
+def _is_multipart(request: Request) -> bool:
+    ct = (request.headers.get("content-type") or "").lower()
+    return ct.startswith("multipart/form-data")
 
-def _looks_like_png(data: bytes) -> bool:
-    return len(data) >= len(_PNG_SIGNATURE) and data.startswith(_PNG_SIGNATURE)
 
-
-def _validate_https_url(url: str) -> tuple[bool, str]:
+def _validate_download_url(url: str) -> None:
     try:
         parsed = urlparse(url)
-    except Exception:
-        return False, "Invalid URL."
+    except Exception as exc:
+        raise HTTPException(status_code=400, detail=f"Invalid URL: {exc}") from exc
 
-    if parsed.scheme.lower() != "https":
-        return False, "Only https:// URLs are allowed."
+    if parsed.scheme not in {"http", "https"}:
+        raise HTTPException(status_code=400, detail="Only http/https URLs are supported")
 
-    if not parsed.netloc:
-        return False, "URL must include a hostname."
+    host = (parsed.hostname or "").lower()
+    if not host:
+        raise HTTPException(status_code=400, detail="Invalid URL host")
 
-    hostname = (parsed.hostname or "").strip().lower()
-    if not hostname:
-        return False, "URL must include a hostname."
+    if host in _ALLOWED_HOSTS_EXACT:
+        return
 
-    # Obvious SSRF targets
-    if hostname in {"localhost", "127.0.0.1", "0.0.0.0", "::1"}:
-        return False, "Localhost URLs are not allowed."
+    if any(host == s or host.endswith("." + s) for s in _ALLOWED_HOST_SUFFIXES):
+        return
 
-    # Block private / link-local / reserved IP literals
-    try:
-        ip = ipaddress.ip_address(hostname)
-        if (
-            ip.is_private
-            or ip.is_loopback
-            or ip.is_link_local
-            or ip.is_reserved
-            or ip.is_multicast
-            or ip.is_unspecified
-        ):
-            return False, "Private or non-routable IPs are not allowed."
-    except ValueError:
-        # hostname is not an IP literal; allow (DNS resolution happens in the HTTP client)
-        pass
-
-    # Optional: restrict unusual ports (Actions file URLs are typically 443)
-    if parsed.port not in (None, 443):
-        return False, "Only the default HTTPS port (443) is allowed."
-
-    return True, ""
-
-
-async def _download_png(url: str) -> bytes:
-    ok, reason = _validate_https_url(url)
-    if not ok:
-        raise ValueError(reason)
-
-    # Dedicated client with NO OpenAI auth headers to avoid key leakage.
-    timeout = httpx.Timeout(connect=10.0, read=30.0, write=30.0, pool=10.0)
-    async with httpx.AsyncClient(
-        timeout=timeout,
-        follow_redirects=True,
-        headers={"User-Agent": "chatgpt-team-relay/0.1.0"},
-    ) as client:
-        buf = bytearray()
-        async with client.stream("GET", url) as resp:
-            # Re-validate final URL after redirects.
-            ok, reason = _validate_https_url(str(resp.url))
-            if not ok:
-                raise ValueError(f"Redirected to an unsafe URL: {reason}")
-
-            if resp.status_code >= 400:
-                raise ValueError(f"Failed to download image (HTTP {resp.status_code}).")
+    # Allow specific OpenAI Azure blob hosts (tight pattern)
+    if host.endswith("blob.core.windows.net") and any(host.startswith(p) for p in _ALLOWED_AZURE_BLOBS_PREFIXES):
+        return
+
+    raise HTTPException(status_code=400, detail="Refusing to fetch file URL from an untrusted host")
+
+
+async def _download_bytes(url: str) -> bytes:
+    _validate_download_url(url)
+
+    timeout = httpx.Timeout(20.0, connect=10.0)
+    limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)
 
+    async with httpx.AsyncClient(timeout=timeout, limits=limits, follow_redirects=False) as client:
+        async with client.stream("GET", url, headers={"Accept": "application/octet-stream"}) as resp:
+            if resp.status_code != 200:
+                raise HTTPException(status_code=400, detail=f"Failed to download file (HTTP {resp.status_code})")
+
+            buf = bytearray()
             async for chunk in resp.aiter_bytes():
-                if not chunk:
-                    continue
                 buf.extend(chunk)
-                if len(buf) > _MAX_PNG_BYTES:
-                    raise ValueError("Image is too large (max 4MB).")
+                if len(buf) > _MAX_IMAGE_BYTES:
+                    raise HTTPException(status_code=400, detail="Image exceeds 4 MB limit")
+            return bytes(buf)
 
-    data = bytes(buf)
-    if not _looks_like_png(data):
-        raise ValueError("Downloaded file is not a PNG.")
 
-    return data
+def _ensure_png(data: bytes, *, label: str) -> None:
+    if not data.startswith(_PNG_MAGIC):
+        raise HTTPException(status_code=400, detail=f"Uploaded {label} must be a PNG")
 
 
-def _decode_png_base64(b64: str) -> bytes:
-    b64 = _strip_data_url_prefix(b64.strip())
-    try:
-        raw = base64.b64decode(b64, validate=True)
-    except (binascii.Error, ValueError):
-        raise ValueError("Invalid base64 payload.") from None
+def _as_str_form_value(value: Any) -> str:
+    if value is None:
+        return ""
+    if isinstance(value, bool):
+        return "true" if value else "false"
+    if isinstance(value, (int, float, str)):
+        return str(value)
+    return json.dumps(value, separators=(",", ":"), ensure_ascii=False)
 
-    if len(raw) > _MAX_PNG_BYTES:
-        raise ValueError("Image is too large (max 4MB).")
 
-    if not _looks_like_png(raw):
-        raise ValueError("Decoded file is not a PNG.")
+def _upstream_headers() -> Dict[str, str]:
+    s = get_settings()
+    headers: Dict[str, str] = {
+        "Authorization": f"Bearer {s.OPENAI_API_KEY}",
+        "Accept": "application/json",
+        "Accept-Encoding": "identity",
+    }
+    if s.OPENAI_ORG:
+        headers["OpenAI-Organization"] = s.OPENAI_ORG
+    if s.OPENAI_PROJECT:
+        headers["OpenAI-Project"] = s.OPENAI_PROJECT
+    if s.OPENAI_BETA:
+        headers["OpenAI-Beta"] = s.OPENAI_BETA
+    return headers
+
+
+async def _post_multipart_to_upstream(
+    *,
+    endpoint_path: str,  # must include /v1/...
+    files: Dict[str, Tuple[str, bytes, str]],
+    data: Dict[str, str],
+) -> Response:
+    s = get_settings()
+    upstream_url = s.OPENAI_API_BASE.rstrip("/") + endpoint_path
 
-    return raw
+    timeout = httpx.Timeout(60.0, connect=10.0)
+    limits = httpx.Limits(max_keepalive_connections=10, max_connections=20)
 
+    async with httpx.AsyncClient(timeout=timeout, limits=limits) as client:
+        resp = await client.post(
+            upstream_url,
+            headers=_upstream_headers(),
+            data=data,
+            files=files,
+        )
 
-async def _get_png_bytes(url: Optional[str], b64: Optional[str], param_name: str) -> bytes:
-    if bool(url) == bool(b64):
-        raise ValueError(f"Provide exactly one of {param_name}_url or {param_name}_base64.")
-    if url:
-        return await _download_png(url)
-    return _decode_png_base64(b64 or "")
+    content_type = resp.headers.get("content-type", "application/json")
+    return Response(content=resp.content, status_code=resp.status_code, media_type=content_type)
 
 
-async def _post_upstream_multipart(request: Request, upstream_path: str, *, files: dict[str, Any], data: dict[str, Any]) -> Response:
-    s = get_settings()
-    upstream_url = build_upstream_url(s, upstream_path)
-    headers = build_outbound_headers(
-        request.headers,
-        accept="application/json",
-        forward_accept=False,
-        content_type=None,  # let httpx set multipart boundary
-    )
-
-    client = get_async_httpx_client()
-    upstream_resp = await client.post(
-        upstream_url,
-        headers=headers,
-        data=data,
-        files=files,
-    )
-
-    return Response(
-        content=upstream_resp.content,
-        status_code=upstream_resp.status_code,
-        headers=filter_upstream_headers(upstream_resp.headers),
-        media_type=upstream_resp.headers.get("content-type"),
-    )
-
-
-@router.post("/actions/images/variations", summary="Create image variations (Actions JSON wrapper)")
-async def actions_image_variations(payload: ActionImageVariationsRequest, request: Request) -> Response:
-    """Actions wrapper for /v1/images/variations.
-
-    Accepts file URLs / base64 and performs the required multipart upload server-side.
-    """
-    logger.info("→ [images/actions] POST %s", request.url.path)
+async def _build_variations_multipart(payload: ImagesVariationsJSON) -> Tuple[Dict[str, Tuple[str, bytes, str]], Dict[str, str]]:
+    image_bytes: Optional[bytes] = None
+    image_name = "image.png"
 
-    try:
-        image_bytes = await _get_png_bytes(payload.image_url, payload.image_base64, "image")
-    except ValueError as e:
-        return _error(400, str(e), param="image")
+    # Prefer Actions file refs
+    if payload.openaiFileIdRefs:
+        first = payload.openaiFileIdRefs[0]
+        if not first.download_link:
+            raise HTTPException(status_code=400, detail="openaiFileIdRefs[0].download_link is required")
+        image_bytes = await _download_bytes(first.download_link)
+        image_name = first.name or image_name
+
+    # Fallbacks
+    if image_bytes is None and payload.image_url:
+        image_bytes = await _download_bytes(payload.image_url)
 
-    files = {"image": ("image.png", image_bytes, "image/png")}
-    data: dict[str, Any] = {}
+    if image_bytes is None and payload.image_base64:
+        try:
+            image_bytes = base64.b64decode(payload.image_base64, validate=True)
+        except Exception as exc:
+            raise HTTPException(status_code=400, detail=f"Invalid image_base64: {exc}") from exc
 
-    if payload.n is not None:
-        data["n"] = str(payload.n)
-    if payload.size:
-        data["size"] = payload.size
-    if payload.response_format:
-        data["response_format"] = payload.response_format
-    if payload.model:
-        data["model"] = payload.model
-    if payload.user:
-        data["user"] = payload.user
+    if image_bytes is None:
+        raise HTTPException(status_code=400, detail="Missing image input")
 
-    return await _post_upstream_multipart(request, "/v1/images/variations", files=files, data=data)
+    _ensure_png(image_bytes, label="image")
 
+    files = {"image": (image_name, image_bytes, "image/png")}
 
-@router.post("/actions/images/edits", summary="Edit an image (Actions JSON wrapper)")
-async def actions_image_edits(payload: ActionImageEditsRequest, request: Request) -> Response:
-    """Actions wrapper for /v1/images/edits.
+    form: Dict[str, str] = {}
+    for k in ["model", "n", "size", "response_format", "user"]:
+        v = getattr(payload, k)
+        if v is not None:
+            form[k] = _as_str_form_value(v)
 
-    Accepts file URLs / base64 and performs the required multipart upload server-side.
-    """
-    logger.info("→ [images/actions] POST %s", request.url.path)
+    return files, form
 
-    try:
-        image_bytes = await _get_png_bytes(payload.image_url, payload.image_base64, "image")
-    except ValueError as e:
-        return _error(400, str(e), param="image")
+
+async def _build_edits_multipart(payload: ImagesEditsJSON) -> Tuple[Dict[str, Tuple[str, bytes, str]], Dict[str, str]]:
+    image_bytes: Optional[bytes] = None
+    image_name = "image.png"
 
     mask_bytes: Optional[bytes] = None
-    if payload.mask_url or payload.mask_base64:
+    mask_name = "mask.png"
+
+    if payload.openaiFileIdRefs:
+        first = payload.openaiFileIdRefs[0]
+        if not first.download_link:
+            raise HTTPException(status_code=400, detail="openaiFileIdRefs[0].download_link is required")
+        image_bytes = await _download_bytes(first.download_link)
+        image_name = first.name or image_name
+
+        if len(payload.openaiFileIdRefs) > 1:
+            second = payload.openaiFileIdRefs[1]
+            if second.download_link:
+                mask_bytes = await _download_bytes(second.download_link)
+                mask_name = second.name or mask_name
+
+    if image_bytes is None and payload.image_url:
+        image_bytes = await _download_bytes(payload.image_url)
+
+    if image_bytes is None and payload.image_base64:
         try:
-            mask_bytes = await _get_png_bytes(payload.mask_url, payload.mask_base64, "mask")
-        except ValueError as e:
-            return _error(400, str(e), param="mask")
+            image_bytes = base64.b64decode(payload.image_base64, validate=True)
+        except Exception as exc:
+            raise HTTPException(status_code=400, detail=f"Invalid image_base64: {exc}") from exc
 
-    files = {"image": ("image.png", image_bytes, "image/png")}
+    if image_bytes is None:
+        raise HTTPException(status_code=400, detail="Missing image input")
+
+    _ensure_png(image_bytes, label="image")
+
+    if mask_bytes is None and payload.mask_url:
+        mask_bytes = await _download_bytes(payload.mask_url)
+
+    if mask_bytes is None and payload.mask_base64:
+        try:
+            mask_bytes = base64.b64decode(payload.mask_base64, validate=True)
+        except Exception as exc:
+            raise HTTPException(status_code=400, detail=f"Invalid mask_base64: {exc}") from exc
+
+    if mask_bytes is not None:
+        _ensure_png(mask_bytes, label="mask")
+
+    files: Dict[str, Tuple[str, bytes, str]] = {"image": (image_name, image_bytes, "image/png")}
     if mask_bytes is not None:
-        files["mask"] = ("mask.png", mask_bytes, "image/png")
-
-    data: dict[str, Any] = {"prompt": payload.prompt}
-
-    if payload.n is not None:
-        data["n"] = str(payload.n)
-    if payload.size:
-        data["size"] = payload.size
-    if payload.response_format:
-        data["response_format"] = payload.response_format
-    if payload.model:
-        data["model"] = payload.model
-    if payload.user:
-        data["user"] = payload.user
-
-    return await _post_upstream_multipart(request, "/v1/images/edits", files=files, data=data)
+        files["mask"] = (mask_name, mask_bytes, "image/png")
+
+    form: Dict[str, str] = {}
+    for k in ["prompt", "model", "n", "size", "response_format", "user"]:
+        v = getattr(payload, k)
+        if v is not None:
+            form[k] = _as_str_form_value(v)
+
+    return files, form
+
+
+# --- Standard images routes ---
+
+
+@router.post("/images", summary="Create image generation")
+@router.post("/images/generations", summary="Create image generation (alias)")
+async def create_image(request: Request) -> Response:
+    logger.info("→ [images] %s %s", request.method, request.url.path)
+    return await forward_openai_request(request)
+
+
+@router.post(
+    "/images/variations",
+    summary="Create image variations (multipart or JSON wrapper)",
+    openapi_extra={
+        "requestBody": {
+            "content": {
+                "application/json": {"schema": ImagesVariationsJSON.model_json_schema()},
+            }
+        }
+    },
+)
+async def variations_image(request: Request) -> Response:
+    logger.info("→ [images] %s %s", request.method, request.url.path)
+
+    if _is_multipart(request):
+        return await forward_openai_request(request)
+
+    body = await request.json()
+    payload = ImagesVariationsJSON.model_validate(body)
+    files, form = await _build_variations_multipart(payload)
+    return await _post_multipart_to_upstream(endpoint_path="/v1/images/variations", files=files, data=form)
+
+
+@router.post(
+    "/images/edits",
+    summary="Edit an image (multipart or JSON wrapper)",
+    openapi_extra={
+        "requestBody": {
+            "content": {
+                "application/json": {"schema": ImagesEditsJSON.model_json_schema()},
+            }
+        }
+    },
+)
+async def edit_image(request: Request) -> Response:
+    logger.info("→ [images] %s %s", request.method, request.url.path)
+
+    if _is_multipart(request):
+        return await forward_openai_request(request)
+
+    body = await request.json()
+    payload = ImagesEditsJSON.model_validate(body)
+    files, form = await _build_edits_multipart(payload)
+    return await _post_multipart_to_upstream(endpoint_path="/v1/images/edits", files=files, data=form)
+
+
+# --- Actions-friendly aliases with clean JSON schemas ---
+
+
+@actions_router.post("/variations", summary="Actions JSON wrapper for image variations")
+async def actions_variations(payload: ImagesVariationsJSON) -> Response:
+    files, form = await _build_variations_multipart(payload)
+    return await _post_multipart_to_upstream(endpoint_path="/v1/images/variations", files=files, data=form)
+
+
+@actions_router.post("/edits", summary="Actions JSON wrapper for image edits")
+async def actions_edits(payload: ImagesEditsJSON) -> Response:
+    files, form = await _build_edits_multipart(payload)
+    return await _post_multipart_to_upstream(endpoint_path="/v1/images/edits", files=files, data=form)
diff --git a/app/routes/uploads.py b/app/routes/uploads.py
index 115ee2f..264662d 100644
--- a/app/routes/uploads.py
+++ b/app/routes/uploads.py
@@ -1,68 +1,86 @@
 from __future__ import annotations
 
 import asyncio
+import json
+from typing import Optional
 
 from fastapi import APIRouter, Request
 from fastapi.responses import Response
 
-from app.api.forward_openai import forward_openai_request
-from app.utils.logger import relay_log as logger
+from app.api.forward_openai import forward_openai_method_path, forward_openai_request
 
 router = APIRouter(prefix="/v1", tags=["uploads"])
 
 
-@router.post("/uploads", summary="Create upload")
-async def create_upload(request: Request) -> Response:
-    logger.info("→ [uploads] POST %s", request.url.path)
-    return await forward_openai_request(request)
-
+def _safe_json_from_response(resp: Response) -> Optional[dict]:
+    """
+    Best-effort JSON parse for a Starlette/FastAPI Response created with `content=bytes`.
+    """
+    try:
+        body = getattr(resp, "body", None)
+        if not body:
+            return None
+        if isinstance(body, (bytes, bytearray)):
+            return json.loads(bytes(body).decode("utf-8"))
+        if isinstance(body, str):
+            return json.loads(body)
+    except Exception:
+        return None
+    return None
+
+
+async def _forward_complete_with_retries(request: Request, upload_id: str) -> Response:
+    """
+    Upload completion has occasionally surfaced transient upstream 5xx errors.
+    Since completion is effectively idempotent for a given upload_id, we retry a few times,
+    and finally fall back to GET /uploads/{upload_id} if completion appears to have succeeded.
+    """
+    delays = [0.0, 0.25, 0.75, 1.5]  # seconds (bounded; keeps tests reasonable)
+    last: Optional[Response] = None
 
-@router.get("/uploads/{upload_id}", summary="Get upload")
-async def get_upload(upload_id: str, request: Request) -> Response:
-    logger.info("→ [uploads] GET %s", request.url.path)
-    return await forward_openai_request(request)
+    for delay in delays:
+        if delay:
+            await asyncio.sleep(delay)
 
+        resp = await forward_openai_request(request)
+        last = resp
 
-@router.post("/uploads/{upload_id}/parts", summary="Add upload part")
-async def add_upload_part(upload_id: str, request: Request) -> Response:
-    logger.info("→ [uploads] POST %s", request.url.path)
-    return await forward_openai_request(request)
+        # Any non-5xx we return immediately (includes 2xx, 4xx, etc).
+        if resp.status_code < 500:
+            return resp
 
+    # Fallback: check the upload status (sometimes upstream completed but the response was 5xx).
+    check = await forward_openai_method_path(
+        method="GET",
+        path=f"/v1/uploads/{upload_id}",
+        inbound_headers=request.headers,
+    )
 
-@router.post("/uploads/{upload_id}/complete", summary="Complete upload")
-async def complete_upload(upload_id: str, request: Request) -> Response:
-    """
-    Complete an upload. The upstream endpoint has occasionally returned transient 5xx errors
-    immediately after parts are uploaded. We apply a small retry/backoff to improve reliability.
-    """
-    logger.info("→ [uploads] POST %s", request.url.path)
+    if check.status_code == 200:
+        data = _safe_json_from_response(check)
+        if isinstance(data, dict):
+            status = data.get("status")
+            file_obj = data.get("file")
+            file_id = file_obj.get("id") if isinstance(file_obj, dict) else None
+            if status == "completed" and isinstance(file_id, str) and file_id.startswith("file-"):
+                return check
 
-    resp = await forward_openai_request(request)
+    # Give up and return the last completion attempt.
+    return last or check
 
-    # Retry only on 5xx.
-    if resp.status_code >= 500:
-        for delay in (0.25, 0.75):
-            await asyncio.sleep(delay)
-            logger.info("↻ [uploads] retry complete after %.2fs", delay)
-            resp = await forward_openai_request(request)
-            if resp.status_code < 500:
-                break
 
-    return resp
+# Explicit complete endpoint with retries/fallback.
+@router.post("/uploads/{upload_id}/complete", summary="Complete an upload (with retries)")
+async def uploads_complete(upload_id: str, request: Request) -> Response:
+    return await _forward_complete_with_retries(request, upload_id)
 
 
-@router.post("/uploads/{upload_id}/cancel", summary="Cancel upload")
-async def cancel_upload(upload_id: str, request: Request) -> Response:
-    logger.info("→ [uploads] POST %s", request.url.path)
+# The rest of the uploads API is raw passthrough.
+@router.api_route("/uploads", methods=["POST"], summary="Create an upload")
+async def uploads_create(request: Request) -> Response:
     return await forward_openai_request(request)
 
 
-# Passthrough for any future /uploads subroutes not explicitly defined above.
-@router.api_route(
-    "/uploads/{path:path}",
-    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
-    include_in_schema=False,
-)
-async def uploads_passthrough(path: str, request: Request) -> Response:
-    logger.info("→ [uploads] passthrough %s %s", request.method, request.url.path)
+@router.api_route("/uploads/{path:path}", methods=["GET", "POST", "DELETE"], summary="Uploads passthrough")
+async def uploads_passthrough(request: Request) -> Response:
     return await forward_openai_request(request)
diff --git a/app/utils/authy.py b/app/utils/authy.py
index 9f534d0..aafe161 100755
--- a/app/utils/authy.py
+++ b/app/utils/authy.py
@@ -1,35 +1,66 @@
 from __future__ import annotations
 
-from fastapi import HTTPException, Request
+import hmac
 
-from app.core.config import get_settings
+from fastapi import HTTPException
 
+from app.core.config import settings
 
-def check_relay_key(request: Request) -> None:
+
+def _get_expected_key() -> str:
+    """
+    Prefer settings.RELAY_KEY, but keep a fallback to RELAY_AUTH_TOKEN.
+    """
+    if getattr(settings, "RELAY_KEY", None):
+        return str(settings.RELAY_KEY)
+    token = getattr(settings, "RELAY_AUTH_TOKEN", None)
+    return str(token or "")
+
+
+def check_relay_key(*, authorization: str | None, x_relay_key: str | None) -> None:
     """
-    Validate relay key (client -> relay) when enabled.
+    Validate the inbound request key against settings.RELAY_KEY.
 
-    Expected header name: settings.RELAY_AUTH_HEADER (default: X-Relay-Key)
-    Expected value: settings.RELAY_KEY
+    Accepted locations:
+      - X-Relay-Key: <token>
+      - Authorization: Bearer <token>
 
-    Raises:
-        HTTPException(401) with detail "Missing relay key" or "Invalid relay key"
+    Behavior:
+      - If RELAY_AUTH_ENABLED is false, this is a no-op.
+      - If enabled and no key is configured, raise 500 (misconfiguration).
+      - If missing token, raise 401 "Missing relay key".
+      - If token is invalid, raise 401 "Invalid relay key".
+      - If Authorization is present but not Bearer, raise 401 mentioning Bearer.
     """
-    settings = get_settings()
-    if not settings.RELAY_AUTH_ENABLED:
+    if not getattr(settings, "RELAY_AUTH_ENABLED", False):
         return
 
-    header_name = settings.RELAY_AUTH_HEADER
-    required = settings.RELAY_KEY
+    expected = _get_expected_key().encode("utf-8")
+    if not expected:
+        raise HTTPException(
+            status_code=500,
+            detail="Relay auth misconfigured: RELAY_KEY is empty when auth is enabled",
+        )
 
-    if not required:
-        raise HTTPException(status_code=500, detail="Relay auth enabled but no RELAY_KEY configured")
+    presented: list[str] = []
+    if x_relay_key:
+        presented.append(x_relay_key)
 
-    provided = request.headers.get(header_name)
+    if authorization:
+        parts = authorization.split(" ", 1)
+        if len(parts) == 2 and parts[0].lower() == "bearer":
+            presented.append(parts[1])
+        else:
+            raise HTTPException(
+                status_code=401,
+                detail="Authorization header must use Bearer scheme",
+            )
 
-    # Baseline requires EXACT wording (no trailing period).
-    if provided is None or provided == "":
+    if not presented:
         raise HTTPException(status_code=401, detail="Missing relay key")
 
-    if provided != required:
-        raise HTTPException(status_code=401, detail="Invalid relay key")
+    for token in presented:
+        if hmac.compare_digest(token.encode("utf-8"), expected):
+            return
+
+    raise HTTPException(status_code=401, detail="Invalid relay key")
```

## CURRENT CONTENT OF CHANGED FILES (WORKTREE)

## FILE: app/api/forward_openai.py @ WORKTREE
```
from __future__ import annotations

import gzip
import json
import zlib
from typing import Any, AsyncIterator, Dict, Mapping, Optional
from urllib.parse import urlencode

import httpx
from fastapi import Request
from fastapi.responses import Response, StreamingResponse

from app.core.config import get_settings
from app.core.http_client import get_async_httpx_client, get_async_openai_client

# ---------------------------------------------------------------------------
# Header handling
# ---------------------------------------------------------------------------

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

_STRIP_RESPONSE_HEADERS = {
    *_HOP_BY_HOP_HEADERS,
    "content-encoding",
    "content-length",
}


def _get_setting(settings: object, *names: str, default=None):
    for name in names:
        if hasattr(settings, name):
            val = getattr(settings, name)
            if val is not None:
                return val
    return default


def _openai_api_key(settings: object) -> str:
    return str(_get_setting(settings, "OPENAI_API_KEY", "openai_api_key", default="")).strip()


def _openai_base_url(settings: object) -> str:
    # Accept either OPENAI_API_BASE (includes /v1) or OPENAI_BASE_URL (no /v1).
    api_base = str(_get_setting(settings, "OPENAI_API_BASE", "openai_api_base", default="")).strip()
    base_url = str(_get_setting(settings, "OPENAI_BASE_URL", "openai_base_url", default="")).strip()

    if api_base:
        return api_base
    if base_url:
        return base_url.rstrip("/") + "/v1"
    return "https://api.openai.com/v1"


def _join_url(base: str, path: str) -> str:
    base = base.rstrip("/")
    path = "/" + path.lstrip("/")
    # Avoid /v1/v1 duplication
    if base.endswith("/v1") and path.startswith("/v1/"):
        path = path[len("/v1") :]
    return base + path


def _get_timeout_seconds(settings: Optional[object] = None) -> float:
    """Compatibility helper used by some route modules."""
    s = settings or get_settings()
    return float(
        _get_setting(
            s,
            "PROXY_TIMEOUT_SECONDS",
            "proxy_timeout_seconds",
            "PROXY_TIMEOUT",
            "RELAY_TIMEOUT_SECONDS",
            "RELAY_TIMEOUT",
            default=90.0,
        )
    )


def build_upstream_url(
    path: str,
    *,
    request: Optional[Request] = None,
    base_url: Optional[str] = None,
) -> str:
    """
    Build a full upstream OpenAI URL for the given API path.

    - Handles bases with or without `/v1`
    - Preserves the inbound query string when `request` is provided
    """
    s = get_settings()
    base = (base_url or _openai_base_url(s)).rstrip("/")
    url = _join_url(base, path)

    if request is not None and request.url.query:
        url = url + "?" + request.url.query

    return url


def build_outbound_headers(
    *,
    inbound_headers: Mapping[str, str],
    content_type: Optional[str] = None,
    forward_accept: bool = True,
    accept: Optional[str] = None,
) -> Dict[str, str]:
    """
    Build outbound headers for an upstream OpenAI call.

    - Drops hop-by-hop headers
    - Forces Authorization to our configured OpenAI key
    - Optionally forwards Accept
    - Adds OpenAI-Organization / OpenAI-Project / OpenAI-Beta when configured
    """
    s = get_settings()
    out: Dict[str, str] = {}

    for k, v in inbound_headers.items():
        lk = k.lower()
        if lk in _HOP_BY_HOP_HEADERS:
            continue
        if lk == "authorization":
            continue
        if lk == "content-type":
            continue
        if lk == "accept" and not forward_accept:
            continue
        out[k] = v

    # Force our Authorization header (Bearer).
    out["Authorization"] = f"Bearer {_openai_api_key(s)}"

    if forward_accept:
        if accept:
            out["Accept"] = accept
        elif "accept" in {k.lower() for k in inbound_headers.keys()}:
            # Preserve original case version if present
            for k, v in inbound_headers.items():
                if k.lower() == "accept":
                    out["Accept"] = v
                    break

    if content_type:
        out["Content-Type"] = content_type

    # Optional org/project/beta headers from config.
    org = _get_setting(s, "OPENAI_ORG", "OPENAI_ORGANIZATION", "openai_organization", default=None)
    if org:
        out["OpenAI-Organization"] = str(org)

    project = _get_setting(s, "OPENAI_PROJECT", "openai_project", default=None)
    if project:
        out["OpenAI-Project"] = str(project)

    beta = _get_setting(s, "OPENAI_BETA", "openai_beta", default=None)
    if beta:
        out["OpenAI-Beta"] = str(beta)

    return out


def filter_upstream_headers(up_headers: httpx.Headers) -> Dict[str, str]:
    """
    Filter response headers from upstream to return to the client.

    - Strips hop-by-hop headers
    - Strips content-encoding/content-length because we may decompress/re-chunk
    """
    out: Dict[str, str] = {}
    for k, v in up_headers.items():
        lk = k.lower()
        if lk in _STRIP_RESPONSE_HEADERS:
            continue
        out[k] = v
    return out


def _maybe_decompress(body: bytes, encoding: Optional[str]) -> bytes:
    enc = (encoding or "").lower().strip()
    if not body or not enc:
        return body
    if enc == "gzip":
        return gzip.decompress(body)
    if enc == "deflate":
        try:
            return zlib.decompress(body)
        except zlib.error:
            return zlib.decompress(body, -zlib.MAX_WBITS)
    return body


async def _read_response_bytes(resp: httpx.Response) -> bytes:
    return await resp.aread()


async def forward_openai_request(
    request: Request,
    *,
    method: str,
    path: str,
    json_body: Optional[Any] = None,
    data: Optional[bytes] = None,
    content_type: Optional[str] = None,
    accept: Optional[str] = None,
    stream: bool = False,
) -> Response:
    """
    Forward an inbound FastAPI request to upstream OpenAI, returning a FastAPI Response.

    Supports:
      - JSON requests
      - raw bytes requests (for specific endpoints)
      - streaming (SSE) passthrough when `stream=True`
    """
    s = get_settings()
    timeout_s = _get_timeout_seconds(s)
    http_client = get_async_httpx_client(timeout=timeout_s)

    url = build_upstream_url(path, request=request, base_url=_openai_base_url(s))
    headers = build_outbound_headers(
        inbound_headers=dict(request.headers),
        content_type=content_type,
        forward_accept=True,
        accept=accept,
    )

    if stream:
        async def iter_bytes() -> AsyncIterator[bytes]:
            async with http_client.stream(method, url, headers=headers, json=json_body, content=data) as resp:
                resp.raise_for_status()
                async for chunk in resp.aiter_bytes():
                    if chunk:
                        yield chunk

        return StreamingResponse(
            iter_bytes(),
            status_code=200,
            headers={},  # SSE route typically controls headers separately
            media_type="text/event-stream",
        )

    resp = await http_client.request(method, url, headers=headers, json=json_body, content=data)
    raw = await _read_response_bytes(resp)

    decompressed = _maybe_decompress(raw, resp.headers.get("content-encoding"))
    out_headers = filter_upstream_headers(resp.headers)

    return Response(
        content=decompressed,
        status_code=resp.status_code,
        headers=out_headers,
        media_type=resp.headers.get("content-type"),
    )


def forward_openai_method_path(method: str, path: str):
    """
    Small adapter used by action-friendly proxy routes.
    Returns (method_upper, normalized_path).
    """
    m = (method or "").upper().strip()
    p = "/" + (path or "").lstrip("/")
    return m, p


def _maybe_model_dump(obj: Any) -> Any:
    # OpenAI SDK objects often implement model_dump(); if not, return as-is.
    dump = getattr(obj, "model_dump", None)
    if callable(dump):
        return dump()
    return obj


async def forward_responses_create(payload: Dict[str, Any]) -> Any:
    client = get_async_openai_client()
    result = await client.responses.create(**payload)
    return _maybe_model_dump(result)


async def forward_embeddings_create(payload: Dict[str, Any]) -> Any:
    client = get_async_openai_client()
    result = await client.embeddings.create(**payload)
    return _maybe_model_dump(result)


# ---------------------------------------------------------------------------
# Legacy helper names (kept for backwards compatibility with older route code)
# ---------------------------------------------------------------------------

def _join_upstream_url(base: str, path: str, query: str) -> str:
    """Join base+path and append a pre-encoded query string, avoiding /v1 duplication."""
    url = _join_url(base, path)
    q = (query or "").lstrip("?")
    return f"{url}?{q}" if q else url


def _build_outbound_headers(in_headers: Any) -> Dict[str, str]:
    """Compatibility wrapper for routes that pass `request.headers.items()`."""
    try:
        inbound = {str(k): str(v) for k, v in in_headers}
    except Exception:
        inbound = dict(in_headers) if in_headers is not None else {}
    return build_outbound_headers(inbound_headers=inbound)


def _filter_response_headers(up_headers: httpx.Headers) -> Dict[str, str]:
    """Compatibility wrapper for filtering upstream response headers."""
    return filter_upstream_headers(up_headers)


__all__ = [
    "_get_timeout_seconds",
    "_join_upstream_url",
    "_build_outbound_headers",
    "_filter_response_headers",
    "build_outbound_headers",
    "build_upstream_url",
    "filter_upstream_headers",
    "forward_openai_request",
    "forward_openai_method_path",
    "forward_responses_create",
    "forward_embeddings_create",
]
```

## FILE: app/api/sse.py @ WORKTREE
```
from __future__ import annotations

import json
from typing import Any, Dict

import httpx
from fastapi import APIRouter, Request
from starlette.responses import JSONResponse, Response, StreamingResponse

from app.core.config import settings
from app.core.http_client import get_async_httpx_client
from app.api.forward_openai import _build_outbound_headers, _filter_response_headers, _join_upstream_url  # type: ignore
from app.utils.logger import relay_log as logger

router = APIRouter(prefix="/v1", tags=["sse"])


@router.post("/responses:stream", include_in_schema=False)
async def responses_stream(request: Request) -> Response:
    """
    Compatibility endpoint used by your tests.

    Behavior:
      - Reads JSON body
      - Forces stream=true
      - Proxies to upstream POST /v1/responses
      - Passes upstream SSE through verbatim (no reformatting)
    """
    try:
        payload: Dict[str, Any] = {}
        raw = await request.body()
        if raw:
            payload = json.loads(raw.decode("utf-8"))

        payload["stream"] = True

        upstream_url = _join_upstream_url(settings.OPENAI_API_BASE, "/v1/responses", "")
        headers = _build_outbound_headers(request.headers.items())
        headers["Accept"] = "text/event-stream"
        headers["Content-Type"] = "application/json"

        client = get_async_httpx_client(timeout=float(settings.PROXY_TIMEOUT_SECONDS))
        req = client.build_request("POST", upstream_url, headers=headers, json=payload)
        resp = await client.send(req, stream=True)

        content_type = resp.headers.get("content-type", "text/event-stream")
        filtered_headers = _filter_response_headers(resp.headers)

        if not content_type.lower().startswith("text/event-stream"):
            data = await resp.aread()
            await resp.aclose()
            return Response(
                content=data,
                status_code=resp.status_code,
                headers=filtered_headers,
                media_type=content_type,
            )

        logger.info("↔ upstream SSE POST /v1/responses (via /v1/responses:stream)")

        async def _aiter():
            async for chunk in resp.aiter_bytes():
                yield chunk
            await resp.aclose()

        return StreamingResponse(
            _aiter(),
            status_code=resp.status_code,
            headers=filtered_headers,
            media_type=content_type,
        )

    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        return JSONResponse(status_code=400, content={"detail": "Invalid JSON body", "error": str(exc)})
    except httpx.HTTPError as exc:
        return JSONResponse(status_code=424, content={"detail": "Upstream request failed", "error": str(exc)})
    except Exception as exc:
        return JSONResponse(status_code=424, content={"detail": "Relay wiring error", "error": str(exc)})
```

## FILE: app/api/tools_api.py @ WORKTREE
```
# app/api/tools_api.py
from __future__ import annotations

import copy
from typing import Any, Dict

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.core.config import get_settings

router = APIRouter()


def _build_manifest() -> Dict[str, Any]:
    s = get_settings()

    endpoints = {
        "health": ["/health", "/v1/health"],
        "models": ["/v1/models", "/v1/models/{model}"],
        "responses": [
            "/v1/responses",
            "/v1/responses/{response_id}",
            "/v1/responses/{response_id}/cancel",
            "/v1/responses/{response_id}/input_items",
        ],
        "responses_compact": ["/v1/responses/compact"],
        "embeddings": ["/v1/embeddings"],
        "images": ["/v1/images/generations", "/v1/images/edits", "/v1/images/variations"],
        "images_actions": ["/v1/actions/images/edits", "/v1/actions/images/variations"],
        "files": ["/v1/files", "/v1/files/{file_id}", "/v1/files/{file_id}/content"],
        "uploads": [
            "/v1/uploads",
            "/v1/uploads/{upload_id}",
            "/v1/uploads/{upload_id}/parts",
            "/v1/uploads/{upload_id}/complete",
            "/v1/uploads/{upload_id}/cancel",
        ],
        "batches": ["/v1/batches", "/v1/batches/{batch_id}", "/v1/batches/{batch_id}/cancel"],
        "proxy": ["/v1/proxy"],
        "realtime_http": ["/v1/realtime/sessions"],
        "realtime_ws": ["/v1/realtime/ws"],
    }

    meta = {
        "relay_name": getattr(s, "RELAY_NAME", "chatgpt-team-relay"),
        "auth_required": bool(getattr(s, "RELAY_AUTH_ENABLED", False)),
        "auth_header": "X-Relay-Key",
        "upstream_base_url": getattr(s, "UPSTREAM_BASE_URL", getattr(s, "OPENAI_API_BASE", "")),
        "actions_openapi_url": "/openapi.actions.json",
        "actions_openapi_groups": [
            "health",
            "models",
            "responses",
            "responses_compact",
            "embeddings",
            "images",
            "images_actions",
            "proxy",
            "realtime_http",
        ],
    }

    # Provide both "old" and "new" shapes for compatibility:
    return {
        "object": "relay.manifest",
        "data": {"endpoints": endpoints, "meta": meta},
        "endpoints": endpoints,
        "meta": meta,
    }


@router.get("/manifest", include_in_schema=False)
@router.get("/v1/manifest", include_in_schema=False)
async def get_manifest() -> Dict[str, Any]:
    return _build_manifest()


@router.get("/openapi.actions.json", include_in_schema=False)
async def openapi_actions(request: Request) -> JSONResponse:
    """
    Curated OpenAPI subset for ChatGPT Actions (REST; no WebSocket client).
    """
    full = request.app.openapi()
    manifest = _build_manifest()

    groups = (manifest.get("meta") or {}).get("actions_openapi_groups") or []
    endpoints = manifest.get("endpoints") or {}
    allowed_paths: set[str] = set()

    for g in groups:
        allowed_paths.update(endpoints.get(str(g), []) or [])

    allowed_paths.update({"/health", "/v1/health"})

    filtered = copy.deepcopy(full)
    filtered["paths"] = {p: spec for p, spec in (full.get("paths") or {}).items() if p in allowed_paths}

    info = filtered.get("info") or {}
    title = str(info.get("title") or "OpenAPI")
    info["title"] = f"{title} (Actions subset)"
    filtered["info"] = info

    return JSONResponse(filtered)
```

## FILE: app/core/config.py @ WORKTREE
```
from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import List, Optional


def _env(key: str, default: Optional[str] = None) -> str:
    val = os.getenv(key)
    if val is None:
        return "" if default is None else default
    return val


def _bool_env(key: str, default: bool = False) -> bool:
    val = os.getenv(key)
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "yes", "y", "on")


def _csv_env(key: str, default: Optional[List[str]] = None) -> List[str]:
    val = os.getenv(key)
    if val is None:
        return [] if default is None else default
    parts = [p.strip() for p in val.split(",")]
    return [p for p in parts if p]


def _normalize_url(url: str) -> str:
    url = (url or "").strip()
    return url.rstrip("/") if url else ""


def _strip_v1(url: str) -> str:
    url = _normalize_url(url)
    if url.endswith("/v1"):
        return url[: -len("/v1")]
    return url


@dataclass(slots=True)
class Settings:
    # --- App / relay identity ---
    app_mode: str = field(default_factory=lambda: _env("APP_MODE", "dev"))
    relay_name: str = field(default_factory=lambda: _env("RELAY_NAME", "openai-relay"))

    # --- OpenAI / upstream configuration (canonical = lower_snake_case) ---
    openai_api_key: str = field(default_factory=lambda: _env("OPENAI_API_KEY", ""))
    openai_organization: str = field(
        default_factory=lambda: _env("OPENAI_ORG_ID", _env("OPENAI_ORGANIZATION", ""))
    )
    openai_project: str = field(default_factory=lambda: _env("OPENAI_PROJECT_ID", ""))
    openai_beta: str = field(default_factory=lambda: _env("OPENAI_BETA", ""))

    # Root base URL (no /v1) and API base URL (includes /v1). You can set either:
    # - OPENAI_BASE_URL=https://api.openai.com
    # - OPENAI_API_BASE=https://api.openai.com/v1
    openai_base_url: str = field(default_factory=lambda: _env("OPENAI_BASE_URL", ""))
    openai_api_base: str = field(
        default_factory=lambda: _env("OPENAI_API_BASE", "https://api.openai.com/v1")
    )

    # --- Relay auth / runtime ---
    relay_auth_enabled: bool = field(default_factory=lambda: _bool_env("RELAY_AUTH_ENABLED", False))
    relay_key: str = field(default_factory=lambda: _env("RELAY_KEY", ""))
    relay_auth_header: str = field(default_factory=lambda: _env("RELAY_AUTH_HEADER", "X-Relay-Key"))
    relay_timeout_seconds: float = field(default_factory=lambda: float(_env("RELAY_TIMEOUT_SECONDS", "120")))

    # --- Defaults / misc ---
    default_model: str = field(default_factory=lambda: _env("DEFAULT_MODEL", _env("RELAY_MODEL", "gpt-5.1")))

    cors_allow_origins: List[str] = field(default_factory=lambda: _csv_env("CORS_ALLOW_ORIGINS", ["*"]))
    cors_allow_methods: List[str] = field(default_factory=lambda: _csv_env("CORS_ALLOW_METHODS", ["*"]))
    cors_allow_headers: List[str] = field(default_factory=lambda: _csv_env("CORS_ALLOW_HEADERS", ["*"]))
    cors_allow_credentials: bool = field(default_factory=lambda: _bool_env("CORS_ALLOW_CREDENTIALS", True))

    log_level: str = field(default_factory=lambda: _env("LOG_LEVEL", "INFO"))
    environment: str = field(default_factory=lambda: _env("ENVIRONMENT", "dev"))

    def __post_init__(self) -> None:
        # Normalize and reconcile URLs.
        self.openai_base_url = _normalize_url(self.openai_base_url)
        self.openai_api_base = _normalize_url(self.openai_api_base)

        if self.openai_base_url:
            self.openai_api_base = f"{self.openai_base_url}/v1"
        else:
            base = _strip_v1(self.openai_api_base)
            self.openai_base_url = base or "https://api.openai.com"
            self.openai_api_base = f"{self.openai_base_url}/v1"

        # Best-effort logging level (do not crash if logging misconfigured).
        try:
            logging.getLogger().setLevel(self.log_level.upper())
        except Exception:
            pass

    def validate(self) -> None:
        if not self.openai_base_url:
            raise ValueError("openai_base_url must not be empty")
        if self.relay_auth_enabled and not self.relay_key:
            raise ValueError("RELAY_AUTH_ENABLED=true requires RELAY_KEY to be set")

    # -------------------------------------------------------------------------
    # Legacy / compatibility aliases (upper-case properties)
    # -------------------------------------------------------------------------

    @property
    def APP_MODE(self) -> str:
        return self.app_mode

    @APP_MODE.setter
    def APP_MODE(self, value: str) -> None:
        self.app_mode = value or self.app_mode

    @property
    def RELAY_NAME(self) -> str:
        return self.relay_name

    @RELAY_NAME.setter
    def RELAY_NAME(self, value: str) -> None:
        self.relay_name = value or self.relay_name

    @property
    def OPENAI_API_KEY(self) -> str:
        return self.openai_api_key

    @OPENAI_API_KEY.setter
    def OPENAI_API_KEY(self, value: str) -> None:
        self.openai_api_key = value or ""

    @property
    def OPENAI_ORG_ID(self) -> str:
        return self.openai_organization

    @OPENAI_ORG_ID.setter
    def OPENAI_ORG_ID(self, value: str) -> None:
        self.openai_organization = value or ""

    @property
    def OPENAI_PROJECT_ID(self) -> str:
        return self.openai_project

    @OPENAI_PROJECT_ID.setter
    def OPENAI_PROJECT_ID(self, value: str) -> None:
        self.openai_project = value or ""

    @property
    def OPENAI_API_BASE(self) -> str:
        return self.openai_api_base

    @OPENAI_API_BASE.setter
    def OPENAI_API_BASE(self, value: str) -> None:
        api_base = _normalize_url(value)
        base = _strip_v1(api_base)
        self.openai_base_url = base or "https://api.openai.com"
        self.openai_api_base = f"{self.openai_base_url}/v1"

    @property
    def OPENAI_BASE_URL(self) -> str:
        """Legacy/compat alias for `openai_base_url` (no `/v1`)."""
        return self.openai_base_url

    @OPENAI_BASE_URL.setter
    def OPENAI_BASE_URL(self, value: str) -> None:
        base = _normalize_url(value)
        self.openai_base_url = base or "https://api.openai.com"
        self.openai_api_base = f"{self.openai_base_url}/v1"

    @property
    def OPENAI_ORG(self) -> str:
        return self.openai_organization

    @OPENAI_ORG.setter
    def OPENAI_ORG(self, value: str) -> None:
        self.openai_organization = value or ""

    @property
    def OPENAI_ORGANIZATION(self) -> str:
        return self.openai_organization

    @OPENAI_ORGANIZATION.setter
    def OPENAI_ORGANIZATION(self, value: str) -> None:
        self.openai_organization = value or ""

    @property
    def OPENAI_PROJECT(self) -> str:
        return self.openai_project

    @OPENAI_PROJECT.setter
    def OPENAI_PROJECT(self, value: str) -> None:
        self.openai_project = value or ""

    @property
    def UPSTREAM_BASE_URL(self) -> str:
        return self.openai_base_url

    @UPSTREAM_BASE_URL.setter
    def UPSTREAM_BASE_URL(self, value: str) -> None:
        base = _normalize_url(value)
        self.openai_base_url = base or "https://api.openai.com"
        self.openai_api_base = f"{self.openai_base_url}/v1"

    @property
    def RELAY_AUTH_ENABLED(self) -> bool:
        return self.relay_auth_enabled

    @RELAY_AUTH_ENABLED.setter
    def RELAY_AUTH_ENABLED(self, value: bool) -> None:
        self.relay_auth_enabled = bool(value)

    @property
    def RELAY_KEY(self) -> str:
        return self.relay_key

    @RELAY_KEY.setter
    def RELAY_KEY(self, value: str) -> None:
        self.relay_key = value or ""

    @property
    def RELAY_AUTH_HEADER(self) -> str:
        return self.relay_auth_header

    @RELAY_AUTH_HEADER.setter
    def RELAY_AUTH_HEADER(self, value: str) -> None:
        self.relay_auth_header = value or "X-Relay-Key"

    @property
    def RELAY_TIMEOUT_SECONDS(self) -> float:
        return self.relay_timeout_seconds

    @RELAY_TIMEOUT_SECONDS.setter
    def RELAY_TIMEOUT_SECONDS(self, value: float) -> None:
        self.relay_timeout_seconds = float(value)

    @property
    def PROXY_TIMEOUT_SECONDS(self) -> float:
        """Compat alias used by some proxy/SSE routes."""
        return self.relay_timeout_seconds

    @PROXY_TIMEOUT_SECONDS.setter
    def PROXY_TIMEOUT_SECONDS(self, value: float) -> None:
        self.relay_timeout_seconds = float(value)

    @property
    def PROXY_TIMEOUT(self) -> float:
        return self.relay_timeout_seconds

    @PROXY_TIMEOUT.setter
    def PROXY_TIMEOUT(self, value: float) -> None:
        self.relay_timeout_seconds = float(value)

    @property
    def PROXY_TIMEOUT_S(self) -> float:
        return self.relay_timeout_seconds

    @PROXY_TIMEOUT_S.setter
    def PROXY_TIMEOUT_S(self, value: float) -> None:
        self.relay_timeout_seconds = float(value)

    @property
    def RELAY_TIMEOUT(self) -> float:
        return self.relay_timeout_seconds

    @RELAY_TIMEOUT.setter
    def RELAY_TIMEOUT(self, value: float) -> None:
        self.relay_timeout_seconds = float(value)

    @property
    def RELAY_TIMEOUT_S(self) -> float:
        return self.relay_timeout_seconds

    @RELAY_TIMEOUT_S.setter
    def RELAY_TIMEOUT_S(self, value: float) -> None:
        self.relay_timeout_seconds = float(value)

    @property
    def OPENAI_TIMEOUT(self) -> float:
        return self.relay_timeout_seconds

    @OPENAI_TIMEOUT.setter
    def OPENAI_TIMEOUT(self, value: float) -> None:
        self.relay_timeout_seconds = float(value)

    @property
    def OPENAI_TIMEOUT_S(self) -> float:
        return self.relay_timeout_seconds

    @OPENAI_TIMEOUT_S.setter
    def OPENAI_TIMEOUT_S(self, value: float) -> None:
        self.relay_timeout_seconds = float(value)

    @property
    def DEFAULT_MODEL(self) -> str:
        return self.default_model

    @DEFAULT_MODEL.setter
    def DEFAULT_MODEL(self, value: str) -> None:
        self.default_model = value or self.default_model

    @property
    def CORS_ALLOW_ORIGINS(self) -> List[str]:
        return self.cors_allow_origins

    @CORS_ALLOW_ORIGINS.setter
    def CORS_ALLOW_ORIGINS(self, value: List[str]) -> None:
        self.cors_allow_origins = list(value or [])

    @property
    def CORS_ALLOW_METHODS(self) -> List[str]:
        return self.cors_allow_methods

    @CORS_ALLOW_METHODS.setter
    def CORS_ALLOW_METHODS(self, value: List[str]) -> None:
        self.cors_allow_methods = list(value or [])

    @property
    def CORS_ALLOW_HEADERS(self) -> List[str]:
        return self.cors_allow_headers

    @CORS_ALLOW_HEADERS.setter
    def CORS_ALLOW_HEADERS(self, value: List[str]) -> None:
        self.cors_allow_headers = list(value or [])

    @property
    def CORS_ALLOW_CREDENTIALS(self) -> bool:
        return self.cors_allow_credentials

    @CORS_ALLOW_CREDENTIALS.setter
    def CORS_ALLOW_CREDENTIALS(self, value: bool) -> None:
        self.cors_allow_credentials = bool(value)

    @property
    def LOG_LEVEL(self) -> str:
        return self.log_level

    @LOG_LEVEL.setter
    def LOG_LEVEL(self, value: str) -> None:
        self.log_level = value or self.log_level

    @property
    def ENVIRONMENT(self) -> str:
        return self.environment

    @ENVIRONMENT.setter
    def ENVIRONMENT(self, value: str) -> None:
        self.environment = value or self.environment

    # Lowercase compat alias used by some older code
    @property
    def proxy_timeout_seconds(self) -> float:
        return self.relay_timeout_seconds

    @proxy_timeout_seconds.setter
    def proxy_timeout_seconds(self, value: float) -> None:
        self.relay_timeout_seconds = float(value)


_settings_cache: Optional[Settings] = None


def get_settings() -> Settings:
    global _settings_cache
    if _settings_cache is None:
        _settings_cache = Settings()
        _settings_cache.validate()
    return _settings_cache


# Singleton (tests may monkeypatch attributes on this instance)
settings = get_settings()


__all__ = ["Settings", "get_settings", "settings"]
```

## FILE: app/core/http_client.py @ WORKTREE
```
from __future__ import annotations

import asyncio
import os
from typing import Dict, Optional, Tuple

import httpx
from openai import AsyncOpenAI

from app.core.config import get_settings

# Cache clients per-event-loop and timeout to avoid cross-loop reuse issues.
# Key: (id(loop), timeout_seconds)
_LOOP_CLIENTS: Dict[Tuple[int, float], Tuple[httpx.AsyncClient, AsyncOpenAI]] = {}


def _get_or_set_loop() -> asyncio.AbstractEventLoop:
    """
    Returns the running loop if available. If called from a sync context (e.g. python -c),
    creates and sets a new event loop so client construction remains usable.
    """
    try:
        return asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop


def _resolve_openai_api_base(settings: object) -> str:
    """
    Resolve the upstream OpenAI API base.

    IMPORTANT: Prefer OPENAI_API_BASE / settings.openai_api_base over OPENAI_BASE_URL to avoid
    accidentally pointing back to the relay itself.
    """
    candidate = (
        getattr(settings, "openai_api_base", None)
        or os.getenv("OPENAI_API_BASE")
        or os.getenv("OPENAI_API_BASE_URL")
    )
    if not candidate:
        candidate = "https://api.openai.com/v1"
    return str(candidate).rstrip("/")


def _resolve_openai_api_key(settings: object) -> Optional[str]:
    return getattr(settings, "openai_api_key", None) or os.getenv("OPENAI_API_KEY")


def _resolve_timeout_seconds(settings: object, timeout: Optional[float]) -> float:
    if timeout is not None:
        return float(timeout)

    # Try common project-level settings fields first (kept flexible for refactors).
    for attr in ("proxy_timeout_seconds", "relay_timeout_seconds", "openai_timeout_seconds"):
        val = getattr(settings, attr, None)
        if val is not None:
            return float(val)

    # Environment fallback
    env_val = os.getenv("RELAY_TIMEOUT_SECONDS")
    if env_val:
        try:
            return float(env_val)
        except ValueError:
            pass

    # Safe default
    return 60.0


def _get_or_create_clients(timeout_seconds: float) -> Tuple[httpx.AsyncClient, AsyncOpenAI]:
    loop = _get_or_set_loop()
    cache_key = (id(loop), float(timeout_seconds))

    existing = _LOOP_CLIENTS.get(cache_key)
    if existing is not None:
        return existing

    settings = get_settings()
    base_url = _resolve_openai_api_base(settings)
    api_key = _resolve_openai_api_key(settings)

    headers = {"User-Agent": "chatgpt-team-relay/1.0"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    httpx_client = httpx.AsyncClient(
        base_url=base_url,
        timeout=float(timeout_seconds),
        headers=headers,
    )

    openai_kwargs = {"base_url": base_url, "http_client": httpx_client}
    if api_key:
        openai_kwargs["api_key"] = api_key

    openai_client = AsyncOpenAI(**openai_kwargs)

    _LOOP_CLIENTS[cache_key] = (httpx_client, openai_client)
    return httpx_client, openai_client


def get_async_httpx_client(timeout: Optional[float] = None) -> httpx.AsyncClient:
    """
    Shared AsyncClient for upstream OpenAI HTTP calls (used by forward/proxy routes).
    """
    settings = get_settings()
    effective_timeout = _resolve_timeout_seconds(settings, timeout)
    httpx_client, _ = _get_or_create_clients(effective_timeout)
    return httpx_client


def get_async_openai_client(timeout: Optional[float] = None) -> AsyncOpenAI:
    """
    Shared AsyncOpenAI client (SDK-backed calls).
    """
    settings = get_settings()
    effective_timeout = _resolve_timeout_seconds(settings, timeout)
    _, openai_client = _get_or_create_clients(effective_timeout)
    return openai_client


async def close_async_clients() -> None:
    """
    Close cached clients for the *current* event loop.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # No running loop; close everything to avoid leaks in CLI contexts.
        await aclose_all_clients()
        return

    loop_id = id(loop)
    keys_to_close = [k for k in _LOOP_CLIENTS.keys() if k[0] == loop_id]

    for key in keys_to_close:
        httpx_client, _ = _LOOP_CLIENTS.pop(key)
        await httpx_client.aclose()


async def aclose_all_clients() -> None:
    """
    Close all cached clients across all loops (primarily for tests / shutdown hooks).
    """
    items = list(_LOOP_CLIENTS.items())
    _LOOP_CLIENTS.clear()

    for _, (httpx_client, _) in items:
        await httpx_client.aclose()
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

## FILE: app/main.py @ WORKTREE
```
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as api_router
from app.api.sse import router as sse_router
from app.api.tools_api import router as tools_router
from app.core.config import get_settings
from app.middleware.p4_orchestrator import P4OrchestratorMiddleware
from app.middleware.relay_auth import RelayAuthMiddleware
from app.middleware.validation import ValidationMiddleware


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=getattr(settings, "RELAY_NAME", "ChatGPT Team Relay"),
        version="0.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
    )

    # Middlewares (order: last added runs first)
    app.add_middleware(P4OrchestratorMiddleware)

    # Always install RelayAuthMiddleware; it no-ops when RELAY_AUTH_ENABLED is false.
    app.add_middleware(RelayAuthMiddleware)

    app.add_middleware(ValidationMiddleware)

    # Routers
    app.include_router(sse_router)
    app.include_router(tools_router)
    app.include_router(api_router)

    return app


app = create_app()
```

## FILE: app/middleware/relay_auth.py @ WORKTREE
```
from __future__ import annotations

from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import settings


_PUBLIC_PATHS = {
    "/health",
    "/v1/health",
    "/manifest",
    "/openapi.json",
    "/openapi.actions.json",
}


def _extract_relay_key(request: Request) -> Optional[str]:
    # Preferred header
    x_key = request.headers.get("X-Relay-Key")
    if x_key:
        return x_key.strip()

    # Bearer fallback
    auth = request.headers.get("Authorization") or ""
    auth = auth.strip()
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()

    return None


class RelayAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Allow unauthenticated access to public endpoints (health/openapi/manifest).
        if request.url.path in _PUBLIC_PATHS or request.url.path.startswith("/static/"):
            return await call_next(request)

        if not settings.RELAY_AUTH_ENABLED:
            return await call_next(request)

        provided = _extract_relay_key(request)
        if not provided:
            return JSONResponse(status_code=401, content={"detail": "Missing relay key"})

        if provided != settings.RELAY_KEY:
            return JSONResponse(status_code=401, content={"detail": "Invalid relay key"})

        return await call_next(request)
```

## FILE: app/routes/images.py @ WORKTREE
```
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

from app.api.forward_openai import forward_openai_request
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
    if s.OPENAI_ORG:
        headers["OpenAI-Organization"] = s.OPENAI_ORG
    if s.OPENAI_PROJECT:
        headers["OpenAI-Project"] = s.OPENAI_PROJECT
    if s.OPENAI_BETA:
        headers["OpenAI-Beta"] = s.OPENAI_BETA
    return headers


async def _post_multipart_to_upstream(
    *,
    endpoint_path: str,  # must include /v1/...
    files: Dict[str, Tuple[str, bytes, str]],
    data: Dict[str, str],
) -> Response:
    s = get_settings()
    upstream_url = s.OPENAI_API_BASE.rstrip("/") + endpoint_path

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
```

## FILE: app/routes/uploads.py @ WORKTREE
```
from __future__ import annotations

import asyncio
import json
from typing import Optional

from fastapi import APIRouter, Request
from fastapi.responses import Response

from app.api.forward_openai import forward_openai_method_path, forward_openai_request

router = APIRouter(prefix="/v1", tags=["uploads"])


def _safe_json_from_response(resp: Response) -> Optional[dict]:
    """
    Best-effort JSON parse for a Starlette/FastAPI Response created with `content=bytes`.
    """
    try:
        body = getattr(resp, "body", None)
        if not body:
            return None
        if isinstance(body, (bytes, bytearray)):
            return json.loads(bytes(body).decode("utf-8"))
        if isinstance(body, str):
            return json.loads(body)
    except Exception:
        return None
    return None


async def _forward_complete_with_retries(request: Request, upload_id: str) -> Response:
    """
    Upload completion has occasionally surfaced transient upstream 5xx errors.
    Since completion is effectively idempotent for a given upload_id, we retry a few times,
    and finally fall back to GET /uploads/{upload_id} if completion appears to have succeeded.
    """
    delays = [0.0, 0.25, 0.75, 1.5]  # seconds (bounded; keeps tests reasonable)
    last: Optional[Response] = None

    for delay in delays:
        if delay:
            await asyncio.sleep(delay)

        resp = await forward_openai_request(request)
        last = resp

        # Any non-5xx we return immediately (includes 2xx, 4xx, etc).
        if resp.status_code < 500:
            return resp

    # Fallback: check the upload status (sometimes upstream completed but the response was 5xx).
    check = await forward_openai_method_path(
        method="GET",
        path=f"/v1/uploads/{upload_id}",
        inbound_headers=request.headers,
    )

    if check.status_code == 200:
        data = _safe_json_from_response(check)
        if isinstance(data, dict):
            status = data.get("status")
            file_obj = data.get("file")
            file_id = file_obj.get("id") if isinstance(file_obj, dict) else None
            if status == "completed" and isinstance(file_id, str) and file_id.startswith("file-"):
                return check

    # Give up and return the last completion attempt.
    return last or check


# Explicit complete endpoint with retries/fallback.
@router.post("/uploads/{upload_id}/complete", summary="Complete an upload (with retries)")
async def uploads_complete(upload_id: str, request: Request) -> Response:
    return await _forward_complete_with_retries(request, upload_id)


# The rest of the uploads API is raw passthrough.
@router.api_route("/uploads", methods=["POST"], summary="Create an upload")
async def uploads_create(request: Request) -> Response:
    return await forward_openai_request(request)


@router.api_route("/uploads/{path:path}", methods=["GET", "POST", "DELETE"], summary="Uploads passthrough")
async def uploads_passthrough(request: Request) -> Response:
    return await forward_openai_request(request)
```

## FILE: app/utils/authy.py @ WORKTREE
```
from __future__ import annotations

import hmac

from fastapi import HTTPException

from app.core.config import settings


def _get_expected_key() -> str:
    """
    Prefer settings.RELAY_KEY, but keep a fallback to RELAY_AUTH_TOKEN.
    """
    if getattr(settings, "RELAY_KEY", None):
        return str(settings.RELAY_KEY)
    token = getattr(settings, "RELAY_AUTH_TOKEN", None)
    return str(token or "")


def check_relay_key(*, authorization: str | None, x_relay_key: str | None) -> None:
    """
    Validate the inbound request key against settings.RELAY_KEY.

    Accepted locations:
      - X-Relay-Key: <token>
      - Authorization: Bearer <token>

    Behavior:
      - If RELAY_AUTH_ENABLED is false, this is a no-op.
      - If enabled and no key is configured, raise 500 (misconfiguration).
      - If missing token, raise 401 "Missing relay key".
      - If token is invalid, raise 401 "Invalid relay key".
      - If Authorization is present but not Bearer, raise 401 mentioning Bearer.
    """
    if not getattr(settings, "RELAY_AUTH_ENABLED", False):
        return

    expected = _get_expected_key().encode("utf-8")
    if not expected:
        raise HTTPException(
            status_code=500,
            detail="Relay auth misconfigured: RELAY_KEY is empty when auth is enabled",
        )

    presented: list[str] = []
    if x_relay_key:
        presented.append(x_relay_key)

    if authorization:
        parts = authorization.split(" ", 1)
        if len(parts) == 2 and parts[0].lower() == "bearer":
            presented.append(parts[1])
        else:
            raise HTTPException(
                status_code=401,
                detail="Authorization header must use Bearer scheme",
            )

    if not presented:
        raise HTTPException(status_code=401, detail="Missing relay key")

    for token in presented:
        if hmac.compare_digest(token.encode("utf-8"), expected):
            return

    raise HTTPException(status_code=401, detail="Invalid relay key")
```

