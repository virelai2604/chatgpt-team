# ChatGPT Sync
Repo: chatgpt-team
Base: origin/main
Generated: 2025-12-18T15:13:15+07:00

## FILE: app/api/forward_openai.py
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
    from app.core.config import settings as _settings  # type: ignore

    def get_settings():
        return _settings


# -------------------------
# URL + header normalization
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
    """Normalize base to scheme://host[:port] (no trailing /, no /v1)."""
    base = (base_url or "").strip()
    if not base:
        return "https://api.openai.com"
    base = base.rstrip("/")
    if base.endswith("/v1"):
        base = base[: -len("/v1")]
    return base.rstrip("/")


def normalize_upstream_path(path: str) -> str:
    """Ensure path starts with /v1."""
    p = (path or "").strip()
    if not p.startswith("/"):
        p = "/" + p
    if not p.startswith("/v1/") and p != "/v1":
        # allow callers to pass "/responses" or "/v1/responses"
        if p.startswith("/"):
            p = "/v1" + p
        else:
            p = "/v1/" + p
    return p


def build_upstream_url(path: str) -> str:
    settings = get_settings()
    base = normalize_base_url(getattr(settings, "openai_base_url", "https://api.openai.com"))
    p = normalize_upstream_path(path)
    return f"{base}{p}"


def filter_upstream_headers(headers: Mapping[str, str]) -> dict[str, str]:
    """Strip hop-by-hop headers and anything that shouldn't be forwarded back to the client."""
    out: dict[str, str] = {}
    for k, v in headers.items():
        lk = k.lower()
        if lk in _HOP_BY_HOP_HEADERS:
            continue
        # Let FastAPI/Uvicorn manage content-length/transfer-encoding.
        if lk in {"content-length", "transfer-encoding"}:
            continue
        out[k] = v
    return out


def build_outbound_headers(
    inbound_headers: Optional[Mapping[str, str]] = None,
    *,
    content_type: Optional[str] = None,
    accept: Optional[str] = None,
) -> dict[str, str]:
    """Build headers for upstream OpenAI call.

    - Uses server-side OpenAI API key
    - Does NOT forward inbound Authorization
    - Forwards safe headers (User-Agent, OpenAI-Organization/Project, etc.)
    """
    settings = get_settings()
    api_key = getattr(settings, "openai_api_key", None)
    if not api_key:
        raise HTTPException(status_code=500, detail="Server is missing OPENAI_API_KEY")

    outbound: dict[str, str] = {
        "Authorization": f"Bearer {api_key}",
    }

    if inbound_headers:
        passthrough_allow = {
            "user-agent",
            "openai-organization",
            "openai-project",
            "openai-beta",
        }
        for k, v in inbound_headers.items():
            lk = k.lower()
            if lk in passthrough_allow:
                outbound[k] = v

    if content_type:
        outbound["Content-Type"] = content_type
    if accept:
        outbound["Accept"] = accept

    return outbound


def _normalize_query_params(query: Optional[Mapping[str, Any]]) -> list[tuple[str, str]]:
    if not query:
        return []
    items: list[tuple[str, str]] = []
    for k, v in query.items():
        if v is None:
            continue
        if isinstance(v, (list, tuple)):
            for vv in v:
                if vv is None:
                    continue
                items.append((str(k), str(vv)))
        else:
            items.append((str(k), str(v)))
    return items


def _get_timeout_seconds(request: Optional[Request] = None) -> float:
    """Centralized request timeout selection."""
    settings = get_settings()
    timeout = getattr(settings, "proxy_timeout_seconds", None)
    if timeout is None:
        timeout = getattr(settings, "relay_timeout_seconds", 120)
    try:
        return float(timeout)
    except Exception:
        return 120.0


def _maybe_model_dump(obj: Any) -> Any:
    """Convert OpenAI SDK objects to plain JSON-serializable dicts when possible."""
    if obj is None:
        return None
    if hasattr(obj, "model_dump"):
        try:
            return obj.model_dump()
        except Exception:
            pass
    if hasattr(obj, "dict"):
        try:
            return obj.dict()
        except Exception:
            pass
    return obj


# -------------------------
# Generic passthrough forwarder
# -------------------------

async def forward_openai_request(request: Request, upstream_path: str) -> Response:
    """Forward an inbound FastAPI request to OpenAI upstream.

    Supports:
    - JSON requests
    - multipart/form-data uploads (streamed)
    - SSE streaming responses (if upstream returns text/event-stream)
    - binary responses
    """
    upstream_url = build_upstream_url(upstream_path)
    timeout = _get_timeout_seconds(request)

    # Decide whether to stream request body
    content_type = request.headers.get("content-type", "")
    is_multipart = content_type.startswith("multipart/form-data")

    outbound_headers = build_outbound_headers(
        request.headers,
        content_type=None if is_multipart else content_type or None,
        accept=request.headers.get("accept"),
    )

    client = get_async_httpx_client()

    relay_log.info("Forwarding %s %s", request.method, upstream_path)

    if is_multipart:
        # Stream body directly to upstream (avoid buffering large uploads)
        async def body_iter():
            async for chunk in request.stream():
                yield chunk

        upstream_resp = await client.request(
            method=request.method,
            url=upstream_url,
            headers=outbound_headers,
            params=request.query_params,
            content=body_iter(),
            timeout=timeout,
        )
    else:
        raw = await request.body()
        upstream_resp = await client.request(
            method=request.method,
            url=upstream_url,
            headers=outbound_headers,
            params=request.query_params,
            content=raw if raw else None,
            timeout=timeout,
        )

    media_type = upstream_resp.headers.get("content-type")

    # If SSE, stream it through
    if media_type and media_type.startswith("text/event-stream"):
        async def sse_stream():
            async for line in upstream_resp.aiter_lines():
                yield (line + "\n").encode("utf-8")

        return StreamingResponse(
            sse_stream(),
            status_code=upstream_resp.status_code,
            headers=filter_upstream_headers(upstream_resp.headers),
            media_type=media_type,
        )

    # Otherwise, return buffered content
    content = await upstream_resp.aread()
    return Response(
        content=content,
        status_code=upstream_resp.status_code,
        headers=filter_upstream_headers(upstream_resp.headers),
        media_type=media_type,
    )


# -------------------------
# JSON-envelope proxy helper
# -------------------------

async def forward_openai_method_path(
    *,
    method: str,
    path: str,
    request: Optional[Request] = None,
    query: Optional[Mapping[str, Any]] = None,
    json_body: Optional[Any] = None,
    body: Optional[Any] = None,
    inbound_headers: Optional[Mapping[str, str]] = None,
    headers: Optional[Mapping[str, str]] = None,
) -> Response:
    """Forward an OpenAI API call expressed as method + path (+ optional JSON + query).

    This is used by the /v1/proxy route (JSON envelope).
    """

    # Backward-compatible aliases:
    # - some callers pass `headers=` instead of `inbound_headers=`
    # - some callers pass `body=` instead of `json_body=`
    if inbound_headers is None and headers is not None:
        inbound_headers = headers
    if inbound_headers is None and request is not None:
        inbound_headers = request.headers
    if json_body is None and body is not None:
        json_body = body

    upstream_url = build_upstream_url(path)
    timeout = _get_timeout_seconds(request)

    params = _normalize_query_params(query)
    content_type = "application/json" if json_body is not None else None
    outbound_headers = build_outbound_headers(inbound_headers, content_type=content_type)

    client = get_async_httpx_client()

    payload_bytes: Optional[bytes] = None
    if json_body is not None:
        payload_bytes = json.dumps(json_body).encode("utf-8")

    relay_log.info("Proxy-forward %s %s", method.upper(), path)

    upstream_resp = await client.request(
        method=method.upper(),
        url=upstream_url,
        headers=outbound_headers,
        params=params,
        content=payload_bytes,
        timeout=timeout,
    )

    media_type = upstream_resp.headers.get("content-type")
    content = await upstream_resp.aread()

    return Response(
        content=content,
        status_code=upstream_resp.status_code,
        headers=filter_upstream_headers(upstream_resp.headers),
        media_type=media_type,
    )


# -------------------------
# Higher-level helpers used by routes
# -------------------------

async def forward_responses_create(*, request: Request) -> dict[str, Any]:
    client = get_async_openai_client()
    payload = await request.json()
    relay_log.info("Forward /v1/responses via SDK")
    result = await client.responses.create(**payload)
    return _maybe_model_dump(result)


async def forward_embeddings_create(*, request: Request) -> dict[str, Any]:
    client = get_async_openai_client()
    payload = await request.json()
    relay_log.info("Forward /v1/embeddings via SDK")
    result = await client.embeddings.create(**payload)
    return _maybe_model_dump(result)


async def forward_files_list(*, request: Request) -> dict[str, Any]:
    client = get_async_openai_client()
    params = dict(request.query_params)
    result = await client.files.list(**params)
    return _maybe_model_dump(result)


async def forward_files_create(*, request: Request) -> dict[str, Any]:
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

## FILE: app/core/http_client.py
```
from __future__ import annotations

import asyncio
from typing import Any, Dict, Tuple

import httpx
from openai import AsyncOpenAI

from app.core.config import get_settings
from app.utils.logger import get_logger

log = get_logger(__name__)

# Cache per-event-loop to avoid "attached to a different loop" issues with reload.
_LOOP_CLIENTS: Dict[int, Tuple[httpx.AsyncClient, AsyncOpenAI]] = {}


def _loop_id() -> int:
    try:
        return id(asyncio.get_running_loop())
    except RuntimeError:
        # No running loop (import-time / sync context). Use a stable sentinel.
        return -1


def get_async_httpx_client() -> httpx.AsyncClient:
    loop_key = _loop_id()
    if loop_key in _LOOP_CLIENTS:
        return _LOOP_CLIENTS[loop_key][0]

    settings = get_settings()
    timeout = httpx.Timeout(getattr(settings, "relay_timeout_seconds", 120.0))
    client = httpx.AsyncClient(timeout=timeout)
    openai_client = AsyncOpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        http_client=client,
    )
    _LOOP_CLIENTS[loop_key] = (client, openai_client)
    return client


def get_async_openai_client() -> AsyncOpenAI:
    loop_key = _loop_id()
    if loop_key in _LOOP_CLIENTS:
        return _LOOP_CLIENTS[loop_key][1]

    # Ensure both are created together (shared httpx client)
    get_async_httpx_client()
    return _LOOP_CLIENTS[loop_key][1]


async def close_async_clients() -> None:
    """Close the cached clients for the current event loop."""
    loop_key = _loop_id()
    if loop_key not in _LOOP_CLIENTS:
        return

    client, _ = _LOOP_CLIENTS.pop(loop_key)
    try:
        await client.aclose()
    except Exception:
        log.exception("Failed closing httpx client")


async def aclose_all_clients() -> None:
    """Close all cached clients across loops (best-effort)."""
    items = list(_LOOP_CLIENTS.items())
    _LOOP_CLIENTS.clear()
    for _, (client, _) in items:
        try:
            await client.aclose()
        except Exception:
            log.exception("Failed closing httpx client")
```

## FILE: app/routes/proxy.py
```
from __future__ import annotations

import re
from typing import Any, Mapping, Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response
from pydantic import AliasChoices, BaseModel, Field, model_validator

from app.api.forward_openai import forward_openai_method_path
from app.core.auth import require_relay_auth
from app.utils.logger import relay_log

router = APIRouter(prefix="/v1", tags=["proxy"])

# -----------------------------------------------------------------------------
# Proxy policy
#
# This endpoint is intentionally restricted: it only forwards a curated subset
# of OpenAI routes and blocks internal/admin routes.
# -----------------------------------------------------------------------------

_BLOCKED_PREFIXES = (
    "/v1/admin",
    "/admin",
    "/internal",
    "/v1/internal",
)

# Each entry: (allowed_methods, regex_pattern)
_ALLOWED_ROUTES: list[tuple[set[str], re.Pattern[str]]] = [
    # ---- Responses (metadata only; streaming handled via /v1/responses route) ----
    ({"POST"}, re.compile(r"^/v1/responses$")),
    ({"GET"}, re.compile(r"^/v1/responses/[^/]+$")),
    ({"DELETE"}, re.compile(r"^/v1/responses/[^/]+$")),
    ({"POST"}, re.compile(r"^/v1/responses/[^/]+/cancel$")),

    # ---- Embeddings ----
    ({"POST"}, re.compile(r"^/v1/embeddings$")),

    # ---- Models ----
    ({"GET"}, re.compile(r"^/v1/models$")),
    ({"GET"}, re.compile(r"^/v1/models/[^/]+$")),

    # ---- Files (metadata only; binary content handled by /v1/files routes) ----
    ({"GET"}, re.compile(r"^/v1/files$")),
    ({"GET"}, re.compile(r"^/v1/files/[^/]+$")),
    ({"DELETE"}, re.compile(r"^/v1/files/[^/]+$")),

    # ---- Vector stores (metadata only) ----
    ({"GET", "POST"}, re.compile(r"^/v1/vector_stores$")),
    ({"GET", "POST", "DELETE"}, re.compile(r"^/v1/vector_stores/[^/]+$")),

    # ---- Containers (metadata only) ----
    ({"GET", "POST"}, re.compile(r"^/v1/containers$")),
    ({"GET", "POST", "DELETE"}, re.compile(r"^/v1/containers/[^/]+$")),

    # ---- Conversations (metadata only) ----
    ({"POST"}, re.compile(r"^/v1/conversations$")),
    ({"GET"}, re.compile(r"^/v1/conversations/[^/]+$")),
    ({"DELETE"}, re.compile(r"^/v1/conversations/[^/]+$")),

    # ---- Batches (metadata only) ----
    ({"GET", "POST"}, re.compile(r"^/v1/batches$")),
    ({"GET"}, re.compile(r"^/v1/batches/[^/]+$")),
    ({"POST"}, re.compile(r"^/v1/batches/[^/]+/cancel$")),

    # ---- Videos (metadata only; create/content are handled by /v1/videos routes) ----
    ({"GET"}, re.compile(r"^/v1/videos$")),
    ({"GET"}, re.compile(r"^/v1/videos/[^/]+$")),
    ({"POST"}, re.compile(r"^/v1/videos/[^/]+/remix$")),
    ({"DELETE"}, re.compile(r"^/v1/videos/[^/]+$")),
]


def _is_blocked(path: str) -> bool:
    p = (path or "").strip()
    return any(p.startswith(prefix) for prefix in _BLOCKED_PREFIXES)


def _is_allowed(method: str, path: str) -> bool:
    m = (method or "").upper().strip()
    p = (path or "").strip()
    for allowed_methods, pattern in _ALLOWED_ROUTES:
        if m in allowed_methods and pattern.match(p):
            return True
    return False


class ProxyRequest(BaseModel):
    method: str = Field(..., description="HTTP method to call upstream (GET/POST/DELETE/...)")
    path: str = Field(..., description="Upstream OpenAI path, e.g. /v1/videos/...")
    query: Optional[Mapping[str, Any]] = Field(default=None, description="Query params to send upstream")

    # Accept body under multiple common names
    body: Optional[Any] = Field(
        default=None,
        validation_alias=AliasChoices("body", "json", "payload"),
        description="JSON body (optional)",
    )

    @model_validator(mode="after")
    def _normalize(self) -> "ProxyRequest":
        self.method = (self.method or "").upper().strip()
        self.path = (self.path or "").strip()
        return self


@router.post("/proxy")
async def proxy(call: ProxyRequest, request: Request) -> Response:
    require_relay_auth(request)

    if _is_blocked(call.path):
        raise HTTPException(status_code=403, detail="Path blocked by policy")

    if not _is_allowed(call.method, call.path):
        raise HTTPException(status_code=403, detail="Route not allowlisted for proxy")

    relay_log.info("Proxy call: %s %s", call.method, call.path)

    return await forward_openai_method_path(
        method=call.method,
        path=call.path,
        query=call.query,
        json_body=call.body,
        inbound_headers=request.headers,
    )
```

## FILE: app/utils/http_client.py
```
from __future__ import annotations

"""Compatibility shim.

Historically some modules imported HTTP/OpenAI clients from `app.utils.http_client`.
The canonical implementation lives in `app.core.http_client`.

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
```

## FILE: app/utils/logger.py
```
from __future__ import annotations

import logging
import os
from typing import Optional

_LOGGER_ROOT_NAME = "chatgpt_team_relay"


def configure_logging(level: Optional[str] = None) -> None:
    """Idempotent logging setup for local dev and production.

    - Uses a single StreamHandler to stdout
    - Avoids duplicate handlers on reload
    - Sets a clean, grep-friendly format
    """
    resolved_level = (level or os.getenv("LOG_LEVEL") or "INFO").upper()
    root_logger = logging.getLogger(_LOGGER_ROOT_NAME)

    # Idempotency: don't stack handlers on reload.
    if getattr(root_logger, "_relay_configured", False):
        root_logger.setLevel(resolved_level)
        return

    root_logger.setLevel(resolved_level)
    root_logger.propagate = False

    handler = logging.StreamHandler()
    handler.setLevel(resolved_level)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )

    root_logger.addHandler(handler)
    setattr(root_logger, "_relay_configured", True)


def get_logger(name: str) -> logging.Logger:
    """Return a namespaced logger under the relay root."""
    if not name:
        return logging.getLogger(_LOGGER_ROOT_NAME)
    return logging.getLogger(f"{_LOGGER_ROOT_NAME}.{name}")


# Default logger used across the codebase.
relay_log = get_logger("relay")


# ---------------------------------------------------------------------------
# Backward-compatible convenience functions.
# Some older route modules imported these directly (e.g., `from app.utils.logger import info`).
# ---------------------------------------------------------------------------

def debug(msg: str, *args, **kwargs) -> None:
    relay_log.debug(msg, *args, **kwargs)


def info(msg: str, *args, **kwargs) -> None:
    relay_log.info(msg, *args, **kwargs)


def warning(msg: str, *args, **kwargs) -> None:
    relay_log.warning(msg, *args, **kwargs)


# Common alias
warn = warning


def error(msg: str, *args, **kwargs) -> None:
    relay_log.error(msg, *args, **kwargs)


def exception(msg: str, *args, **kwargs) -> None:
    relay_log.exception(msg, *args, **kwargs)
```

## FILE: project-tree.md
```
  📄 .env
  📄 .env.example.env
  📄 .gitattributes
  📄 .gitignore
  📄 AGENTS.md
  📄 ChatGPT-API_reference_ground_truth-2025-10-29.pdf
  📄 __init__.py
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
    📄 conversations.csv
    📄 conversations.db
    📁 conversations
      📄 conversations.db
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
    📄 test_relay_auth_guard.py
    📁 downloads```

