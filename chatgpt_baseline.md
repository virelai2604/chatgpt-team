# ChatGPT Sync
Repo: chatgpt-team
Base: origin/main
Base commit (merge-base): 4a039730f9a85ddb91f1a6f031321c2d232c27e1
Dirs: app tests static schemas
Root files: project-tree.md pyproject.toml
Mode: baseline
Generated: 2025-12-22T12:31:44+07:00

## TREE (repo root at 4a039730f9a85ddb91f1a6f031321c2d232c27e1)
```
 - .env.example.env
 - .gitattributes
 - .github
 - .gitignore
 - .gitleaks.toml
 - AGENTS.md
 - ChatGPT-API_reference_ground_truth-2025-10-29.pdf
 - __init__.py
 - app
 - chatgpt_baseline.md
 - chatgpt_changes.md
 - chatgpt_sync.sh
 - data
 - docs
 - generate_tree.py
 - openai_models_2025-11.csv
 - project-tree.md
 - pyproject.toml
 - pytest.ini
 - render.yaml
 - requirements.txt
 - schemas
 - static
 - tests
```

## TREE (app/ at 4a039730f9a85ddb91f1a6f031321c2d232c27e1)
```
 - app/__init__.py
 - app/api/__init__.py
 - app/api/forward_openai.py
 - app/api/routes.py
 - app/api/sse.py
 - app/api/tools_api.py
 - app/core/__init__.py
 - app/core/config.py
 - app/core/http_client.py
 - app/core/logging.py
 - app/main.py
 - app/manifests/__init__.py
 - app/manifests/tools_manifest.json
 - app/middleware/__init__.py
 - app/middleware/p4_orchestrator.py
 - app/middleware/relay_auth.py
 - app/middleware/validation.py
 - app/routes/__init__.py
 - app/routes/actions.py
 - app/routes/batches.py
 - app/routes/containers.py
 - app/routes/conversations.py
 - app/routes/embeddings.py
 - app/routes/files.py
 - app/routes/health.py
 - app/routes/images.py
 - app/routes/models.py
 - app/routes/proxy.py
 - app/routes/realtime.py
 - app/routes/register_routes.py
 - app/routes/responses.py
 - app/routes/uploads.py
 - app/routes/vector_stores.py
 - app/routes/videos.py
 - app/utils/__init__.py
 - app/utils/authy.py
 - app/utils/error_handler.py
 - app/utils/http_client.py
 - app/utils/logger.py
```

## TREE (tests/ at 4a039730f9a85ddb91f1a6f031321c2d232c27e1)
```
 - tests/__init__.py
 - tests/client.py
 - tests/conftest.py
 - tests/test_local_e2e.py
 - tests/test_relay_auth_guard.py
```

## TREE (static/ at 4a039730f9a85ddb91f1a6f031321c2d232c27e1)
```
 - static/.well-known/__init__.py
 - static/.well-known/ai-plugin.json
```

## TREE (schemas/ at 4a039730f9a85ddb91f1a6f031321c2d232c27e1)
```
 - schemas/__init__.py
 - schemas/openapi.yaml
```

## BASELINE (ROOT FILES)

## FILE: project-tree.md @ 4a039730f9a85ddb91f1a6f031321c2d232c27e1
```
  📄 .env
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

## FILE: pyproject.toml @ 4a039730f9a85ddb91f1a6f031321c2d232c27e1
```
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "chatgpt-team-relay"
version = "0.1.0"
description = "OpenAI-compatible relay server for ChatGPT Team (FastAPI + OpenAI Python SDK)."
readme = "docs/README.md"
requires-python = ">=3.12"

dependencies = [
  "fastapi>=0.115,<1.0",
  "uvicorn[standard]>=0.32,<1.0",
  "httpx>=0.27,<1.0",

  "openai>=2.11.0,<3.0",

  "python-dotenv>=1.0,<2.0",
  "pydantic>=2.5,<3.0",
  "pydantic-settings>=2.2,<3.0",

  "python-multipart>=0.0.18,<0.1.0",
  "sse-starlette>=2.1,<3.0",

  "orjson>=3.9,<4.0",
  "pyyaml>=6.0,<7.0",
  "loguru>=0.7,<1.0",
]

[project.optional-dependencies]
dev = [
  "pytest>=8.3,<9.0",
  "pytest-asyncio>=0.23,<1.0",
  "pytest-env>=1.1,<2.0",
  "pytest-dotenv>=0.5,<1.0",
  "pytest-httpx>=0.30,<1.0",
  "pytest-mock>=3.14,<4.0",
  "requests>=2.32,<3.0",
  "requests-mock>=1.12,<2.0",
  "anyio>=4.4,<5.0",
]

[project.urls]
homepage = "https://github.com/virelai2604/chatgpt-team"
repository = "https://github.com/virelai2604/chatgpt-team"
issues = "https://github.com/virelai2604/chatgpt-team/issues"

# -----------------------------------------
# Setuptools: include ONLY app and app.*
# -----------------------------------------
[tool.setuptools.packages.find]
where = ["."]
include = ["app*"]
exclude = ["tests*", "docs*", "render*"]

# Include non-.py files needed at runtime (tools manifest, etc.)
[tool.setuptools.package-data]
app = ["manifests/*.json"]
```

## BASELINE (app/)

## FILE: app/__init__.py @ 4a039730f9a85ddb91f1a6f031321c2d232c27e1
```
```

## FILE: app/api/__init__.py @ 4a039730f9a85ddb91f1a6f031321c2d232c27e1
```
```

## FILE: app/api/forward_openai.py @ 4a039730f9a85ddb91f1a6f031321c2d232c27e1
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

## FILE: app/api/routes.py @ 4a039730f9a85ddb91f1a6f031321c2d232c27e1
```
# app/api/routes.py

from __future__ import annotations

from fastapi import APIRouter

from app.routes.register_routes import register_routes
from app.utils.logger import get_logger

logger = get_logger(__name__)

# This router is included by app.main and mirrors all route families under /v1.
router = APIRouter()

# Delegate wiring to the shared register_routes helper.
register_routes(router)

logger.info("API router initialized with shared route families")
```

## FILE: app/api/sse.py @ 4a039730f9a85ddb91f1a6f031321c2d232c27e1
```
# app/api/sse.py
from __future__ import annotations

import json
from typing import Any, AsyncIterator, Dict, Iterable, Optional, Union

from fastapi import APIRouter, Body
from fastapi.responses import StreamingResponse

from app.core.http_client import get_async_openai_client
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/v1", tags=["openai-relay-streaming"])

SSEByteSource = Union[Iterable[bytes], AsyncIterator[bytes]]


def format_sse_event(
    *,
    event: str,
    data: str,
    id: Optional[str] = None,
    retry: Optional[int] = None,
) -> bytes:
    lines = []
    if id is not None:
        lines.append(f"id: {id}")
    if event:
        lines.append(f"event: {event}")

    if data == "":
        lines.append("data:")
    else:
        for line in data.splitlines():
            lines.append(f"data: {line}")

    if retry is not None:
        lines.append(f"retry: {retry}")

    payload = "\n".join(lines) + "\n\n"
    return payload.encode("utf-8")


def sse_error_event(message: str, code: Optional[str] = None, *, id: Optional[str] = None) -> bytes:
    payload = {"message": message}
    if code:
        payload["code"] = code
    data_str = ";".join([f"{k}={v}" for k, v in payload.items()])
    return format_sse_event(event="error", data=data_str, id=id)


class StreamingSSE(StreamingResponse):
    def __init__(self, content: SSEByteSource, status_code: int = 200, headers: Optional[dict] = None) -> None:
        super().__init__(content=content, status_code=status_code, headers=headers, media_type="text/event-stream")


# Compatibility shim: some older modules imported create_sse_stream from app.api.sse
def create_sse_stream(
    content: SSEByteSource,
    *,
    status_code: int = 200,
    headers: Optional[dict] = None,
) -> StreamingSSE:
    return StreamingSSE(content=content, status_code=status_code, headers=headers)


async def _responses_event_stream(payload: Dict[str, Any]) -> AsyncIterator[bytes]:
    client = get_async_openai_client()
    logger.info("Streaming /v1/responses:stream with payload: %s", payload)

    p = dict(payload)
    p.setdefault("stream", True)

    stream = await client.responses.create(**p)  # stream=True above

    async for event in stream:
        if hasattr(event, "model_dump_json"):
            data_json = event.model_dump_json()
        elif hasattr(event, "model_dump"):
            data_json = json.dumps(event.model_dump(), default=str, separators=(",", ":"))
        else:
            try:
                data_json = json.dumps(event, default=str, separators=(",", ":"))
            except TypeError:
                data_json = json.dumps(str(event))

        yield f"data: {data_json}\n\n".encode("utf-8")

    yield b"data: [DONE]\n\n"


@router.post("/responses:stream")
async def responses_stream(
    body: Dict[str, Any] = Body(..., description="OpenAI Responses.create payload for streaming"),
) -> StreamingSSE:
    return StreamingSSE(_responses_event_stream(body))
```

## FILE: app/api/tools_api.py @ 4a039730f9a85ddb91f1a6f031321c2d232c27e1
```
# ==========================================================
# app/api/tools_api.py — Tools Manifest Endpoints
# ==========================================================
"""
Serves the relay's tools manifest at:
  - GET /manifest
  - GET /v1/manifest

Intent:
  - Option A (Actions-friendly): expose a small, JSON-only tool surface.
  - Full route inventory lives in OpenAPI at /openapi.json.

The integration tests expect:
  data["endpoints"]["responses"] includes "/v1/responses"
  data["endpoints"]["responses_compact"] includes "/v1/responses/compact"
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, cast

from fastapi import APIRouter

from ..core.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["manifest"])


def _read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _extract_tools(payload: Any) -> List[Dict[str, Any]]:
    """
    Accept multiple on-disk shapes safely:
      - {"tools": [...]}                       (legacy)
      - {"data": [...], "object": "list", ...} (what /manifest returns)
      - [...]                                   (raw list of tool dicts)
    """
    if isinstance(payload, list):
        return cast(List[Dict[str, Any]], payload)

    if isinstance(payload, dict):
        tools = payload.get("tools")
        if isinstance(tools, list):
            return cast(List[Dict[str, Any]], tools)

        data = payload.get("data")
        if isinstance(data, list):
            return cast(List[Dict[str, Any]], data)

    return []


def load_tools_manifest() -> List[Dict[str, Any]]:
    """
    Loads tools from:
      1) settings.TOOLS_MANIFEST (if it's a list of tools)
      2) settings.TOOLS_MANIFEST (if it's a path to JSON)
      3) fallback: app/manifests/tools_manifest.json
    """
    settings = get_settings()
    manifest_setting: Union[str, List[Dict[str, Any]], None] = getattr(settings, "TOOLS_MANIFEST", None)

    # If someone injected the tools directly (already parsed)
    if isinstance(manifest_setting, list):
        return manifest_setting

    # If it's a path string
    if isinstance(manifest_setting, str) and manifest_setting.strip():
        path = Path(manifest_setting)
        if path.exists():
            try:
                return _extract_tools(_read_json(path))
            except Exception as e:
                logger.warning("Failed reading TOOLS_MANIFEST from %s: %s", path, e)

    # Fallback to app/manifests/tools_manifest.json relative to this file
    fallback_path = Path(__file__).resolve().parents[1] / "manifests" / "tools_manifest.json"
    if fallback_path.exists():
        try:
            return _extract_tools(_read_json(fallback_path))
        except Exception as e:
            logger.warning("Failed reading fallback tools manifest from %s: %s", fallback_path, e)

    return []


def build_manifest_response(tools: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    settings = get_settings()
    tools_list = tools if tools is not None else load_tools_manifest()

    # Keep current behavior for tests and clients.
    endpoints: Dict[str, List[str]] = {
        # Option A: single Action-friendly proxy entrypoint.
        "proxy": ["/v1/proxy"],
        "responses": ["/v1/responses", "/v1/responses/compact"],
        "responses_compact": ["/v1/responses/compact"],
    }

    relay_name = (
        getattr(settings, "relay_name", None)
        or getattr(settings, "project_name", None)
        or "ChatGPT Team Relay"
    )

    # IMPORTANT: We intentionally do not list multipart/binary families (e.g., /v1/uploads)
    # in this tools manifest. Those routes may exist in the app (see /openapi.json) but are
    # excluded from the Actions-safe tool surface by design.
    meta: Dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "relay_name": relay_name,
        "manifest_scope": "actions_safe",
        "option": "A",
        "openapi_url": "/openapi.json",
        "endpoints_note": (
            "This manifest is a curated, JSON-only tool surface. "
            "Multipart/binary route families (e.g., Uploads) are intentionally excluded; "
            "refer to /openapi.json for the full route inventory."
        ),
    }

    return {
        "object": "list",
        "data": tools_list,
        "endpoints": endpoints,
        "meta": meta,
    }


@router.get("/manifest")
async def get_manifest_root() -> Dict[str, Any]:
    logger.info("Serving tools manifest (root alias)")
    return build_manifest_response()


@router.get("/v1/manifest")
async def get_manifest_v1() -> Dict[str, Any]:
    logger.info("Serving tools manifest (/v1)")
    return build_manifest_response()
```

## FILE: app/core/__init__.py @ 4a039730f9a85ddb91f1a6f031321c2d232c27e1
```
```

## FILE: app/core/config.py @ 4a039730f9a85ddb91f1a6f031321c2d232c27e1
```
from __future__ import annotations

import json
import os
import platform
from dataclasses import dataclass
from functools import lru_cache
from typing import List, Optional


def _env(name: str, default: Optional[str] = None) -> Optional[str]:
    """Read an environment variable with whitespace/empty-string normalization."""
    v = os.getenv(name)
    if v is None:
        return default
    v = v.strip()
    return v if v != "" else default


def _env_bool(name: str, default: bool = False) -> bool:
    v = _env(name)
    if v is None:
        return default
    return v.lower() in {"1", "true", "yes", "y", "on"}


def _env_int(name: str, default: int) -> int:
    v = _env(name)
    if v is None:
        return default
    try:
        return int(v)
    except ValueError:
        return default


def _env_list(name: str, default: Optional[List[str]] = None) -> List[str]:
    """
    Accepts:
      - JSON list: '["https://a.com","https://b.com"]'
      - CSV string: 'https://a.com,https://b.com'
      - single value
    """
    default = default or []
    raw = _env(name)
    if raw is None:
        return list(default)

    raw = raw.strip()
    if raw.startswith("["):
        try:
            data = json.loads(raw)
            if isinstance(data, list):
                out = [str(x).strip() for x in data]
                return [x for x in out if x]
        except Exception:
            return list(default)

    parts = [p.strip() for p in raw.split(",")]
    return [p for p in parts if p]


@dataclass(slots=True)
class Settings:
    # Core service identity
    APP_MODE: str
    ENVIRONMENT: str
    PROJECT_NAME: str
    RELAY_NAME: str
    BIFL_VERSION: str

    # Runtime / diagnostics
    PYTHON_VERSION: str
    LOG_LEVEL: str
    LOG_FORMAT: str
    LOG_COLOR: bool

    # OpenAI upstream
    OPENAI_API_BASE: str
    OPENAI_API_KEY: str
    OPENAI_ORGANIZATION: Optional[str]
    OPENAI_PROJECT: Optional[str]
    OPENAI_BETA: Optional[str]
    OPENAI_ASSISTANTS_BETA: Optional[str]
    OPENAI_REALTIME_BETA: Optional[str]
    OPENAI_MAX_RETRIES: int

    DEFAULT_MODEL: str
    REALTIME_MODEL: str

    # Relay runtime
    RELAY_HOST: str
    RELAY_PORT: int
    RELAY_TIMEOUT_SECONDS: int
    PROXY_TIMEOUT_SECONDS: int

    # Stream / orchestration
    ENABLE_STREAM: bool
    CHAIN_WAIT_MODE: str

    # Relay auth
    RELAY_AUTH_ENABLED: bool
    RELAY_KEY: Optional[str]
    CHATGPT_ACTIONS_SECRET: Optional[str]
    RELAY_AUTH_TOKEN: Optional[str]

    # CORS
    CORS_ALLOW_ORIGINS: List[str]
    CORS_ALLOW_METHODS: List[str]
    CORS_ALLOW_HEADERS: List[str]
    CORS_ALLOW_CREDENTIALS: bool

    # Tools / schema
    TOOLS_MANIFEST: str
    VALIDATION_SCHEMA_PATH: Optional[str]

    # Convenience aliases (snake_case)
    @property
    def environment(self) -> str:
        return self.ENVIRONMENT

    @property
    def project_name(self) -> str:
        return self.PROJECT_NAME

    @property
    def relay_name(self) -> str:
        return self.RELAY_NAME

    @property
    def version(self) -> str:
        return self.BIFL_VERSION

    @property
    def log_level(self) -> str:
        return self.LOG_LEVEL

    @property
    def cors_allow_origins(self) -> List[str]:
        return self.CORS_ALLOW_ORIGINS

    @property
    def cors_allow_methods(self) -> List[str]:
        return self.CORS_ALLOW_METHODS

    @property
    def cors_allow_headers(self) -> List[str]:
        return self.CORS_ALLOW_HEADERS

    @property
    def cors_allow_credentials(self) -> bool:
        return self.CORS_ALLOW_CREDENTIALS

    @property
    def openai_base_url(self) -> str:
        return self.OPENAI_API_BASE

    @property
    def openai_api_key(self) -> str:
        return self.OPENAI_API_KEY

    @property
    def openai_organization(self) -> Optional[str]:
        return self.OPENAI_ORGANIZATION

    @property
    def openai_project(self) -> Optional[str]:
        return self.OPENAI_PROJECT

    @property
    def openai_beta(self) -> Optional[str]:
        return self.OPENAI_BETA

    @property
    def openai_assistants_beta(self) -> Optional[str]:
        return self.OPENAI_ASSISTANTS_BETA

    @property
    def openai_realtime_beta(self) -> Optional[str]:
        return self.OPENAI_REALTIME_BETA

    @property
    def default_model(self) -> str:
        return self.DEFAULT_MODEL

    @property
    def realtime_model(self) -> str:
        return self.REALTIME_MODEL

    @property
    def proxy_timeout_seconds(self) -> int:
        return self.PROXY_TIMEOUT_SECONDS

    @property
    def timeout_seconds(self) -> int:
        # Backward compatible alias
        return self.PROXY_TIMEOUT_SECONDS

    @property
    def max_retries(self) -> int:
        return self.OPENAI_MAX_RETRIES


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    app_mode = _env("APP_MODE", "development") or "development"
    environment = _env("ENVIRONMENT", app_mode) or app_mode

    project_name = _env("PROJECT_NAME", "chatgpt-team-relay") or "chatgpt-team-relay"
    relay_name = _env("RELAY_NAME", "ChatGPT Team Relay") or "ChatGPT Team Relay"
    bifl_version = _env("BIFL_VERSION", "local-dev") or "local-dev"

    python_version = _env("PYTHON_VERSION", platform.python_version()) or platform.python_version()
    log_level = _env("LOG_LEVEL", _env("LOGLEVEL", "INFO") or "INFO") or "INFO"
    log_format = _env("LOG_FORMAT", "plain") or "plain"
    log_color = _env_bool("LOG_COLOR", False)

    openai_api_base = _env("OPENAI_API_BASE", "https://api.openai.com/v1") or "https://api.openai.com/v1"
    # Allow empty key at import-time; enforce on upstream call sites.
    openai_api_key = _env("OPENAI_API_KEY", "") or ""
    openai_org = _env("OPENAI_ORGANIZATION", _env("OPENAI_ORG", None))
    openai_project = _env("OPENAI_PROJECT", None)
    openai_beta = _env("OPENAI_BETA", None)
    openai_assistants_beta = _env("OPENAI_ASSISTANTS_BETA", None)
    openai_realtime_beta = _env("OPENAI_REALTIME_BETA", None)
    openai_max_retries = _env_int("OPENAI_MAX_RETRIES", 3)

    default_model = _env("DEFAULT_MODEL", "gpt-5.1") or "gpt-5.1"
    realtime_model = _env("REALTIME_MODEL", "gpt-realtime") or "gpt-realtime"

    relay_host = _env("RELAY_HOST", "0.0.0.0") or "0.0.0.0"
    relay_port = _env_int("RELAY_PORT", 8000)
    relay_timeout_seconds = _env_int("RELAY_TIMEOUT_SECONDS", _env_int("RELAY_TIMEOUT", 90))
    proxy_timeout_seconds = _env_int("PROXY_TIMEOUT_SECONDS", _env_int("PROXY_TIMEOUT", 90))

    enable_stream = _env_bool("ENABLE_STREAM", True)
    chain_wait_mode = _env("CHAIN_WAIT_MODE", "auto") or "auto"

    relay_auth_enabled = _env_bool("RELAY_AUTH_ENABLED", True)
    relay_key = _env("RELAY_KEY", None)
    chatgpt_actions_secret = _env("CHATGPT_ACTIONS_SECRET", None)
    relay_auth_token = _env("RELAY_AUTH_TOKEN", None)

    cors_allow_origins = _env_list("CORS_ALLOW_ORIGINS", default=["*"])
    cors_allow_methods = _env_list("CORS_ALLOW_METHODS", default=["*"])
    cors_allow_headers = _env_list("CORS_ALLOW_HEADERS", default=["*"])
    cors_allow_credentials = _env_bool("CORS_ALLOW_CREDENTIALS", False)

    tools_manifest = _env("TOOLS_MANIFEST", "tools_manifest.json") or "tools_manifest.json"
    validation_schema_path = _env("VALIDATION_SCHEMA_PATH", None)

    return Settings(
        APP_MODE=app_mode,
        ENVIRONMENT=environment,
        PROJECT_NAME=project_name,
        RELAY_NAME=relay_name,
        BIFL_VERSION=bifl_version,
        PYTHON_VERSION=python_version,
        LOG_LEVEL=log_level,
        LOG_FORMAT=log_format,
        LOG_COLOR=log_color,
        OPENAI_API_BASE=openai_api_base,
        OPENAI_API_KEY=openai_api_key,
        OPENAI_ORGANIZATION=openai_org,
        OPENAI_PROJECT=openai_project,
        OPENAI_BETA=openai_beta,
        OPENAI_ASSISTANTS_BETA=openai_assistants_beta,
        OPENAI_REALTIME_BETA=openai_realtime_beta,
        OPENAI_MAX_RETRIES=openai_max_retries,
        DEFAULT_MODEL=default_model,
        REALTIME_MODEL=realtime_model,
        RELAY_HOST=relay_host,
        RELAY_PORT=relay_port,
        RELAY_TIMEOUT_SECONDS=relay_timeout_seconds,
        PROXY_TIMEOUT_SECONDS=proxy_timeout_seconds,
        ENABLE_STREAM=enable_stream,
        CHAIN_WAIT_MODE=chain_wait_mode,
        RELAY_AUTH_ENABLED=relay_auth_enabled,
        RELAY_KEY=relay_key,
        CHATGPT_ACTIONS_SECRET=chatgpt_actions_secret,
        RELAY_AUTH_TOKEN=relay_auth_token,
        CORS_ALLOW_ORIGINS=cors_allow_origins,
        CORS_ALLOW_METHODS=cors_allow_methods,
        CORS_ALLOW_HEADERS=cors_allow_headers,
        CORS_ALLOW_CREDENTIALS=cors_allow_credentials,
        TOOLS_MANIFEST=tools_manifest,
        VALIDATION_SCHEMA_PATH=validation_schema_path,
    )


# Legacy singleton import pattern used across the codebase
settings: Settings = get_settings()
```

## FILE: app/core/http_client.py @ 4a039730f9a85ddb91f1a6f031321c2d232c27e1
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

## FILE: app/core/logging.py @ 4a039730f9a85ddb91f1a6f031321c2d232c27e1
```
"""
Logging configuration module for the ChatGPT Team Relay.

This bridges the core config with the utility logger. The main entrypoint,
`configure_logging(settings)`, ensures that the global logger is set up
exactly once using the environment-driven values (LOG_LEVEL, LOG_FORMAT, etc.)
defined in :mod:`app.utils.logger`. It accepts a ``settings`` instance but does
not mutate or rely on it; the presence of ``settings`` in the signature
satisfies FastAPI/uvicorn calling conventions.

Consumers should import and call :func:`configure_logging` at application
startup to ensure consistent logging::

    from app.core.logging import configure_logging

    configure_logging(settings)

This design keeps logging configuration centralised while allowing easy
extension in the future.
"""

from __future__ import annotations

from typing import Any

# Importing from app.utils.logger will trigger root logger configuration on
# first call. See app/utils/logger.py for environment-driven behaviour.
from app.utils.logger import get_logger


def configure_logging(settings: Any) -> None:
    """
    Initialise relay logging based on environment variables.

    This function calls into :func:`app.utils.logger.get_logger` which will
    configure the root logger exactly once using the environment variables
    ``LOG_LEVEL``, ``LOG_FORMAT``, and ``LOG_COLOR``. It accepts a
    ``settings`` parameter for interface compatibility, but does not use it
    directly.

    Args:
        settings: settings object (unused but required for API compatibility).
    """
    # Ensure that the root logger is configured. The get_logger call sets up
    # formatting and levels on first invocation.
    get_logger("relay")
```

## FILE: app/main.py @ 4a039730f9a85ddb91f1a6f031321c2d232c27e1
```
from __future__ import annotations

from typing import Callable, Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute

from .api.sse import router as sse_router
from .api.tools_api import router as tools_router
from .core.config import get_settings
from .core.http_client import close_async_clients
from .middleware.p4_orchestrator import P4OrchestratorMiddleware
from .middleware.relay_auth import RelayAuthMiddleware
from .middleware.validation import ValidationMiddleware
from .routes.register_routes import register_routes
from .utils.error_handler import register_exception_handlers
from .utils.logger import configure_logging


def _unique_id_factory() -> Callable[[APIRoute], str]:
    """
    Collision-resistant OpenAPI operationId generator.

    If two routes would otherwise generate the same operationId, we append _2, _3, ...
    This removes FastAPI duplicate operationId warnings even when duplicate routes exist.
    """
    seen: Dict[str, int] = {}

    def _gen(route: APIRoute) -> str:
        methods = "_".join(sorted(route.methods or []))
        path = (route.path_format or route.path).strip("/")
        path = path.replace("/", "_").replace("{", "").replace("}", "")
        name = route.name or getattr(route.endpoint, "__name__", "endpoint")

        base = f"{name}_{methods}_{path}".strip("_")
        n = seen.get(base, 0) + 1
        seen[base] = n
        return base if n == 1 else f"{base}_{n}"

    return _gen


def _get_bool_setting(settings: object, snake: str, upper: str, default: bool) -> bool:
    if hasattr(settings, snake):
        return bool(getattr(settings, snake))
    if hasattr(settings, upper):
        return bool(getattr(settings, upper))
    return default


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(
        title=settings.project_name,
        generate_unique_id_function=_unique_id_factory(),
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
        allow_credentials=settings.cors_allow_credentials,
    )

    relay_auth_enabled = _get_bool_setting(settings, "relay_auth_enabled", "RELAY_AUTH_ENABLED", True)
    if relay_auth_enabled:
        app.add_middleware(RelayAuthMiddleware)

    app.add_middleware(ValidationMiddleware)
    app.add_middleware(P4OrchestratorMiddleware)

    register_routes(app)
    app.include_router(tools_router)
    app.include_router(sse_router)

    register_exception_handlers(app)
    app.add_event_handler("shutdown", close_async_clients)
    return app


app = create_app()
```

## FILE: app/manifests/__init__.py @ 4a039730f9a85ddb91f1a6f031321c2d232c27e1
```
# ==========================================================
# app/manifests/__init__.py — Ground Truth Manifest Loader
# ==========================================================
"""
Loads tools from app/manifests/tools_manifest.json and exposes TOOLS_MANIFEST.

Supports BOTH shapes:
  - {"tools": [ ... ]}   (original intention)
  - {"object":"list","data":[ ... ]} (your current file shape)
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List


_manifest_path = os.path.join(os.path.dirname(__file__), "tools_manifest.json")


def _coerce_tools_list(raw: Any) -> List[Dict[str, Any]]:
    if isinstance(raw, list):
        return [t for t in raw if isinstance(t, dict)]

    if isinstance(raw, dict):
        tools = raw.get("tools")
        if isinstance(tools, list):
            return [t for t in tools if isinstance(t, dict)]

        data = raw.get("data")
        if isinstance(data, list):
            return [t for t in data if isinstance(t, dict)]

    return []


try:
    with open(_manifest_path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    TOOLS_MANIFEST = _coerce_tools_list(raw)
except Exception as e:
    raise RuntimeError(f"Failed to load tools manifest: {_manifest_path} — {e}")
```

## FILE: app/manifests/tools_manifest.json @ 4a039730f9a85ddb91f1a6f031321c2d232c27e1
```
{
  "object": "list",
  "data": [
    {
      "id": "web_search",
      "name": "web_search",
      "object": "tool",
      "type": "function",
      "description": "Search the web for up-to-date information, news, and facts.",
      "parameters": {
        "type": "object",
        "properties": {
          "query": {
            "type": "string",
            "description": "Search query string describing what to look up."
          },
          "recency_days": {
            "type": "integer",
            "description": "How many days back to prioritize in the search (e.g. 1 = last 24h, 7 = last week).",
            "minimum": 1,
            "default": 7
          },
          "max_results": {
            "type": "integer",
            "description": "Maximum number of search results to return.",
            "minimum": 1,
            "maximum": 20,
            "default": 5
          }
        },
        "required": ["query"]
      }
    },
    {
      "id": "file_search",
      "name": "file_search",
      "object": "tool",
      "type": "function",
      "description": "Search user-provided documents or vector stores to retrieve relevant passages.",
      "parameters": {
        "type": "object",
        "properties": {
          "query": {
            "type": "string",
            "description": "Query string describing what information to retrieve from the files."
          },
          "top_k": {
            "type": "integer",
            "description": "Maximum number of chunks or documents to return.",
            "minimum": 1,
            "maximum": 50,
            "default": 8
          },
          "include_metadata": {
            "type": "boolean",
            "description": "Whether to return document metadata (file names, ids, etc.).",
            "default": true
          }
        },
        "required": ["query"]
      }
    },
    {
      "id": "image_generation",
      "name": "image_generation",
      "object": "tool",
      "type": "function",
      "description": "Generate images from natural language prompts using the images API.",
      "parameters": {
        "type": "object",
        "properties": {
          "prompt": {
            "type": "string",
            "description": "Detailed description of the image to generate."
          },
          "size": {
            "type": "string",
            "description": "Requested image size (for example, 512x512, 1024x1024).",
            "default": "1024x1024"
          },
          "n": {
            "type": "integer",
            "description": "Number of images to generate.",
            "minimum": 1,
            "maximum": 10,
            "default": 1
          }
        },
        "required": ["prompt"]
      }
    },
    {
      "id": "code_interpreter",
      "name": "code_interpreter",
      "object": "tool",
      "type": "function",
      "description": "Execute small code snippets (e.g. Python) for calculations, data inspection, and plotting.",
      "parameters": {
        "type": "object",
        "properties": {
          "language": {
            "type": "string",
            "description": "Programming language of the snippet (e.g. 'python').",
            "default": "python"
          },
          "code": {
            "type": "string",
            "description": "The code to execute."
          },
          "stdin": {
            "type": "string",
            "description": "Optional standard input for the process.",
            "nullable": true
          }
        },
        "required": ["code"]
      }
    },
    {
      "id": "mcp_connector",
      "name": "mcp_connector",
      "object": "tool",
      "type": "function",
      "description": "Call an MCP connector/server and invoke one of its tools.",
      "parameters": {
        "type": "object",
        "properties": {
          "server": {
            "type": "string",
            "description": "The MCP server or connector name to call."
          },
          "tool": {
            "type": "string",
            "description": "Tool name on the MCP server to invoke."
          },
          "arguments": {
            "type": "object",
            "description": "JSON object of arguments to pass to the selected tool.",
            "additionalProperties": true,
            "default": {}
          }
        },
        "required": ["server", "tool"]
      }
    },
    {
      "id": "apply_patch",
      "name": "apply_patch",
      "object": "tool",
      "type": "function",
      "description": "Apply structured patches to JSON or text documents (for example, configuration updates).",
      "parameters": {
        "type": "object",
        "properties": {
          "target": {
            "type": "string",
            "description": "Identifier of the target document or resource to patch."
          },
          "patch": {
            "type": "object",
            "description": "Patch payload describing the changes to apply.",
            "additionalProperties": true
          },
          "patch_type": {
            "type": "string",
            "description": "Type of patch to apply (e.g. json_merge, json_patch, text_replace).",
            "default": "json_merge"
          }
        },
        "required": ["target", "patch"]
      }
    },
    {
      "id": "shell",
      "name": "shell",
      "object": "tool",
      "type": "function",
      "description": "Execute shell commands in a controlled environment.",
      "parameters": {
        "type": "object",
        "properties": {
          "command": {
            "type": "string",
            "description": "Shell command to execute."
          },
          "timeout_seconds": {
            "type": "integer",
            "description": "Maximum time in seconds to allow the command to run.",
            "minimum": 1,
            "maximum": 300,
            "default": 60
          },
          "working_directory": {
            "type": "string",
            "description": "Optional working directory for the command.",
            "nullable": true
          }
        },
        "required": ["command"]
      }
    },
    {
      "id": "retrieval",
      "name": "retrieval",
      "object": "tool",
      "type": "function",
      "description": "High-level retrieval wrapper to fetch and synthesize information from multiple sources (files, vector stores, connectors).",
      "parameters": {
        "type": "object",
        "properties": {
          "query": {
            "type": "string",
            "description": "Natural language query describing the information to retrieve."
          },
          "sources": {
            "type": "array",
            "description": "List of logical sources to search over (e.g. ['files', 'web', 'mcp']).",
            "items": {
              "type": "string"
            },
            "default": ["files"]
          },
          "max_items": {
            "type": "integer",
            "description": "Maximum number of items to aggregate.",
            "minimum": 1,
            "maximum": 50,
            "default": 10
          }
        },
        "required": ["query"]
      }
    },
    {
      "id": "computer_use",
      "name": "computer_use",
      "object": "tool",
      "type": "function",
      "description": "Plan and issue high-level computer control actions (for example, open an app, click a button, type text).",
      "parameters": {
        "type": "object",
        "properties": {
          "action": {
            "type": "string",
            "description": "High-level action to perform (e.g. 'open_browser', 'click', 'type')."
          },
          "target": {
            "type": "string",
            "description": "The target element or application when applicable.",
            "nullable": true
          },
          "details": {
            "type": "object",
            "description": "Additional structured parameters for the action.",
            "additionalProperties": true,
            "default": {}
          }
        },
        "required": ["action"]
      }
    },
    {
      "id": "local_shell",
      "name": "local_shell",
      "object": "tool",
      "type": "function",
      "description": "Run shell commands against the local project environment (for example, git status, pytest).",
      "parameters": {
        "type": "object",
        "properties": {
          "command": {
            "type": "string",
            "description": "Command to run inside the local project workspace."
          },
          "timeout_seconds": {
            "type": "integer",
            "description": "Maximum runtime for the command.",
            "minimum": 1,
            "maximum": 300,
            "default": 60
          }
        },
        "required": ["command"]
      }
    }
  ]
}
```

## FILE: app/middleware/__init__.py @ 4a039730f9a85ddb91f1a6f031321c2d232c27e1
```
```

## FILE: app/middleware/p4_orchestrator.py @ 4a039730f9a85ddb91f1a6f031321c2d232c27e1
```
# app/middleware/p4_orchestrator.py
import uuid
from typing import Callable, Awaitable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from ..utils.logger import get_logger

logger = get_logger(__name__)


class P4OrchestratorMiddleware(BaseHTTPMiddleware):
    """
    Simple correlation-ID and request logging middleware aligned with the P4 orchestration idea.
    """

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
        request.state.request_id = request_id

        logger.info(
            "Incoming request",
            extra={"path": str(request.url), "method": request.method, "request_id": request_id},
        )

        response = await call_next(request)
        response.headers["x-request-id"] = request_id
        return response
```

## FILE: app/middleware/relay_auth.py @ 4a039730f9a85ddb91f1a6f031321c2d232c27e1
```
# app/middleware/relay_auth.py

from __future__ import annotations

from typing import Awaitable, Callable

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.utils.authy import check_relay_key
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Exact paths that should always be public
SAFE_EXACT_PATHS = {
    "/",  # root
    "/health",
    "/health/",
    "/v1/health",
    "/v1/health/",
    "/actions/ping",
    "/actions/relay_info",
    "/v1/actions/ping",
    "/v1/actions/relay_info",
}

# Prefixes that should always be public (docs, openapi, assets, etc.)
SAFE_PREFIXES = (
    "/docs",
    "/redoc",
    "/openapi.json",
    "/static",
    "/favicon",
)


class RelayAuthMiddleware(BaseHTTPMiddleware):
    """
    Optional shared-secret auth in front of the relay.

    Controlled by env / settings:

      - RELAY_KEY (or legacy RELAY_AUTH_TOKEN)
      - RELAY_AUTH_ENABLED (bool)

    Behavior:

      - Health + docs + actions ping/info are always public.
      - Non-/v1/ paths remain public.
      - /v1/* paths are protected when RELAY_AUTH_ENABLED is True.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        path = request.url.path

        # Public routes
        if path in SAFE_EXACT_PATHS or path.startswith(SAFE_PREFIXES):
            return await call_next(request)

        # Only protect OpenAI-style API paths under /v1
        if not path.startswith("/v1/"):
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        x_relay_key = request.headers.get("X-Relay-Key")

        try:
            # Will no-op if RELAY_AUTH_ENABLED is False
            check_relay_key(auth_header=auth_header, x_relay_key=x_relay_key)
        except HTTPException as exc:
            # DO NOT let this bubble out as an exception to httpx;
            # convert to a normal JSON error response.
            logger.warning(
                "Relay auth failed",
                extra={"path": path, "method": request.method, "detail": exc.detail},
            )
            return JSONResponse(
                status_code=exc.status_code,
                content={"detail": exc.detail},
                headers=getattr(exc, "headers", None) or {},
            )

        # Auth OK (or disabled)
        return await call_next(request)
```

## FILE: app/middleware/validation.py @ 4a039730f9a85ddb91f1a6f031321c2d232c27e1
```
# app/middleware/validation.py
from typing import Callable, Awaitable

from fastapi import Request
from fastapi.responses import JSONResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware


class ValidationMiddleware(BaseHTTPMiddleware):
    """
    Lightweight request validation middleware.

    - Enforces JSON or multipart Content-Type for mutating requests.
    """

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        if request.method in {"POST", "PUT", "PATCH"}:
            content_type = request.headers.get("content-type", "")
            if (
                "application/json" not in content_type
                and not content_type.startswith("multipart/form-data")
            ):
                return JSONResponse(
                    status_code=415,
                    content={"detail": f"Unsupported Media Type: {content_type!r}"},
                )

        return await call_next(request)
```

## FILE: app/routes/__init__.py @ 4a039730f9a85ddb91f1a6f031321c2d232c27e1
```
# app/routes/__init__.py

from .register_routes import register_routes

__all__ = ["register_routes"]
```

## FILE: app/routes/actions.py @ 4a039730f9a85ddb91f1a6f031321c2d232c27e1
```
# app/routes/actions.py

from __future__ import annotations

from fastapi import APIRouter

from app.core.config import settings

router = APIRouter(tags=["actions"])


def _ping_payload() -> dict:
    """
    Canonical payload for ping-style endpoints.

    Tests assert at least:
      - data["status"] == "ok"            (for /actions/ping)
      - data["source"] == "chatgpt-team-relay"
      - data["app_mode"] non-empty
      - data["environment"] non-empty     (for /v1/actions/ping)
    """
    return {
        "source": "chatgpt-team-relay",
        "status": "ok",
        "app_mode": settings.APP_MODE,
        "environment": settings.ENVIRONMENT,
    }


def _relay_info_payloads() -> tuple[dict, dict]:
    """
    Build both the nested and flat relay-info payloads.

    Nested shape (for /v1/actions/relay_info):

        {
          "type": "relay.info",
          "relay": {
            "name": <relay_name>,
            "app_mode": <app_mode>,
            "environment": <environment>,
          },
          "upstream": {
            "base_url": <openai_base_url>,
            "default_model": <default_model>,
          },
        }

    Flat shape (for /actions/relay_info):

        {
          "relay_name": <relay_name>,
          "environment": <environment>,
          "app_mode": <app_mode>,
          "base_openai_api": <openai_base_url>,
        }

    The tests only assert that the relevant keys exist and are non-empty.
    """
    relay_name = settings.RELAY_NAME or "chatgpt-team-relay"
    app_mode = settings.APP_MODE
    environment = settings.ENVIRONMENT
    base_url = settings.OPENAI_API_BASE
    default_model = settings.DEFAULT_MODEL

    nested = {
        "type": "relay.info",
        "relay": {
            "name": relay_name,
            "app_mode": app_mode,
            "environment": environment,
        },
        "upstream": {
            "base_url": base_url,
            "default_model": default_model,
        },
    }

    flat = {
        "relay_name": relay_name,
        "environment": environment,
        "app_mode": app_mode,
        "base_openai_api": base_url,
    }

    return nested, flat


# ----- ping -----

@router.get("/actions/ping", summary="Simple local ping for tools/tests")
async def actions_ping_root() -> dict:
    """
    Simple ping at /actions/ping.

    tests/test_tools_and_actions_routes.py only checks that:
      - response.status_code == 200
      - response.json()["status"] == "ok"
    Extra fields are allowed.
    """
    return _ping_payload()


@router.get("/v1/actions/ping", summary="Local ping used by orchestrator tests")
async def actions_ping_v1() -> dict:
    """
    Ping under /v1/actions/ping.

    tests/test_actions_and_orchestrator.py requires:
      - status code 200
      - JSON contains non-empty source/status/app_mode/environment
    """
    return _ping_payload()


# ----- relay_info -----

@router.get("/actions/relay_info", summary="Flat relay info for tools")
async def actions_relay_info_root() -> dict:
    """
    Flat relay info at /actions/relay_info.

    tests/test_tools_and_actions_routes.py asserts:
      - data["relay_name"]
      - data["environment"]
      - data["app_mode"]
      - data["base_openai_api"]
    """
    _nested, flat = _relay_info_payloads()
    return flat


@router.get("/v1/actions/relay_info", summary="Structured relay info for orchestrator")
async def actions_relay_info_v1() -> dict:
    """
    Structured relay info at /v1/actions/relay_info.

    tests/test_actions_and_orchestrator.py asserts that:
      - data["type"] == "relay.info"
      - data["relay"]["name"] is non-empty
      - data["relay"]["app_mode"] is non-empty
      - data["relay"]["environment"] is non-empty
      - data["upstream"]["base_url"] is non-empty
      - data["upstream"]["default_model"] is non-empty
    """
    nested, _flat = _relay_info_payloads()
    return nested
```

## FILE: app/routes/batches.py @ 4a039730f9a85ddb91f1a6f031321c2d232c27e1
```
from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import Response

from app.api.forward_openai import forward_openai_request
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/v1/batches")
async def create_batch(request: Request) -> Response:
    logger.info("Incoming /v1/batches create request")
    return await forward_openai_request(request)


@router.get("/v1/batches/{batch_id}")
async def retrieve_batch(batch_id: str, request: Request) -> Response:
    logger.info(f"Incoming /v1/batches retrieve request for batch_id={batch_id}")
    return await forward_openai_request(request)


@router.get("/v1/batches")
async def list_batches(request: Request) -> Response:
    logger.info("Incoming /v1/batches list request")
    return await forward_openai_request(request)


@router.post("/v1/batches/{batch_id}/cancel")
async def cancel_batch(batch_id: str, request: Request) -> Response:
    logger.info(f"Incoming /v1/batches cancel request for batch_id={batch_id}")
    return await forward_openai_request(request)
```

## FILE: app/routes/containers.py @ 4a039730f9a85ddb91f1a6f031321c2d232c27e1
```
from __future__ import annotations

from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import StreamingResponse
from starlette.background import BackgroundTask

from app.api.forward_openai import (
    _get_timeout_seconds,
    build_outbound_headers,
    build_upstream_url,
    filter_upstream_headers,
    forward_openai_request,
)
from app.core.http_client import get_async_httpx_client
from app.utils.logger import relay_log as logger

router = APIRouter(prefix="/v1", tags=["containers"])


async def _forward(request: Request) -> Response:
    logger.info("→ [containers] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


# ---- /v1/containers ----
@router.get("/containers")
async def containers_root_get(request: Request) -> Response:
    return await _forward(request)


@router.post("/containers")
async def containers_root_post(request: Request) -> Response:
    return await _forward(request)


@router.head("/containers", include_in_schema=False)
async def containers_root_head(request: Request) -> Response:
    return await _forward(request)


@router.options("/containers", include_in_schema=False)
async def containers_root_options(request: Request) -> Response:
    return await _forward(request)


async def _container_file_content_head(container_id: str, file_id: str, request: Request) -> Response:
    upstream_path = f"/v1/containers/{container_id}/files/{file_id}/content"
    upstream_url = build_upstream_url(upstream_path)

    headers = build_outbound_headers(
        inbound_headers=request.headers,
        content_type=None,
        forward_accept=True,
        path_hint=upstream_path,
    )

    # Forward Range if provided; otherwise minimal range for headers
    range_hdr: Optional[str] = request.headers.get("range")
    if range_hdr:
        headers["Range"] = range_hdr
    else:
        headers["Range"] = "bytes=0-0"

    client = get_async_httpx_client()
    timeout = _get_timeout_seconds()

    upstream_req = client.build_request(
        method="GET",
        url=upstream_url,
        params=request.query_params,
        headers=headers,
    )

    try:
        upstream_resp = await client.send(upstream_req, stream=True, timeout=timeout, follow_redirects=True)
    except httpx.TimeoutException as exc:
        raise HTTPException(status_code=504, detail=f"Upstream timeout: {type(exc).__name__}") from exc
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail=f"Upstream request failed: {type(exc).__name__}") from exc

    await upstream_resp.aclose()

    return Response(
        content=b"",
        status_code=upstream_resp.status_code,
        headers=filter_upstream_headers(upstream_resp.headers),
        media_type=upstream_resp.headers.get("content-type"),
    )


async def _container_file_content_get(container_id: str, file_id: str, request: Request) -> Response:
    upstream_path = f"/v1/containers/{container_id}/files/{file_id}/content"
    upstream_url = build_upstream_url(upstream_path)

    headers = build_outbound_headers(
        inbound_headers=request.headers,
        content_type=None,
        forward_accept=True,
        path_hint=upstream_path,
    )

    # Forward Range if provided (best-effort)
    range_hdr: Optional[str] = request.headers.get("range")
    if range_hdr:
        headers["Range"] = range_hdr

    client = get_async_httpx_client()
    timeout = _get_timeout_seconds()

    upstream_req = client.build_request(
        method="GET",
        url=upstream_url,
        params=request.query_params,
        headers=headers,
    )

    try:
        upstream_resp = await client.send(upstream_req, stream=True, timeout=timeout, follow_redirects=True)
    except httpx.TimeoutException as exc:
        raise HTTPException(status_code=504, detail=f"Upstream timeout: {type(exc).__name__}") from exc
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail=f"Upstream request failed: {type(exc).__name__}") from exc

    if upstream_resp.status_code >= 400:
        error_body = await upstream_resp.aread()
        await upstream_resp.aclose()
        return Response(
            content=error_body,
            status_code=upstream_resp.status_code,
            headers=filter_upstream_headers(upstream_resp.headers),
            media_type=upstream_resp.headers.get("content-type"),
        )

    return StreamingResponse(
        upstream_resp.aiter_bytes(),
        status_code=upstream_resp.status_code,
        headers=filter_upstream_headers(upstream_resp.headers),
        media_type=upstream_resp.headers.get("content-type"),
        background=BackgroundTask(upstream_resp.aclose),
    )


@router.get("/containers/{container_id}/files/{file_id}/content")
async def container_file_content_get(container_id: str, file_id: str, request: Request) -> Response:
    return await _container_file_content_get(container_id=container_id, file_id=file_id, request=request)


@router.head("/containers/{container_id}/files/{file_id}/content")
async def container_file_content_head(container_id: str, file_id: str, request: Request) -> Response:
    return await _container_file_content_head(container_id=container_id, file_id=file_id, request=request)


@router.api_route(
    "/containers/{path:path}",
    methods=["GET", "POST", "DELETE", "HEAD", "OPTIONS"],
    include_in_schema=False,
)
async def containers_subpaths(path: str, request: Request) -> Response:
    logger.info("→ [containers/*] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)
```

## FILE: app/routes/conversations.py @ 4a039730f9a85ddb91f1a6f031321c2d232c27e1
```
from __future__ import annotations

from fastapi import APIRouter, Request, Response

from app.api.forward_openai import forward_openai_request
from app.utils.logger import relay_log as logger

router = APIRouter(prefix="/v1", tags=["conversations"])


async def _forward(request: Request) -> Response:
    logger.info("→ [conversations] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


# ---- /v1/conversations ----
@router.get("/conversations")
async def conversations_root_get(request: Request) -> Response:
    return await _forward(request)


@router.post("/conversations")
async def conversations_root_post(request: Request) -> Response:
    return await _forward(request)


@router.head("/conversations", include_in_schema=False)
async def conversations_root_head(request: Request) -> Response:
    return await _forward(request)


@router.options("/conversations", include_in_schema=False)
async def conversations_root_options(request: Request) -> Response:
    return await _forward(request)


# ---- /v1/conversations/{path:path} ----
@router.get("/conversations/{path:path}")
async def conversations_subpaths_get(path: str, request: Request) -> Response:
    return await _forward(request)


@router.post("/conversations/{path:path}")
async def conversations_subpaths_post(path: str, request: Request) -> Response:
    return await _forward(request)


@router.patch("/conversations/{path:path}")
async def conversations_subpaths_patch(path: str, request: Request) -> Response:
    return await _forward(request)


@router.delete("/conversations/{path:path}")
async def conversations_subpaths_delete(path: str, request: Request) -> Response:
    return await _forward(request)


@router.head("/conversations/{path:path}", include_in_schema=False)
async def conversations_subpaths_head(path: str, request: Request) -> Response:
    return await _forward(request)


@router.options("/conversations/{path:path}", include_in_schema=False)
async def conversations_subpaths_options(path: str, request: Request) -> Response:
    return await _forward(request)
```

## FILE: app/routes/embeddings.py @ 4a039730f9a85ddb91f1a6f031321c2d232c27e1
```
from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.api.forward_openai import forward_embeddings_create

router = APIRouter(prefix="/v1", tags=["embeddings"])


@router.post("/embeddings")
async def create_embedding(request: Request) -> JSONResponse:
    body: Dict[str, Any] = await request.json()
    resp = await forward_embeddings_create(body)
    payload = resp.model_dump() if hasattr(resp, "model_dump") else resp
    return JSONResponse(content=payload)
```

## FILE: app/routes/files.py @ 4a039730f9a85ddb91f1a6f031321c2d232c27e1
```
from __future__ import annotations

from fastapi import APIRouter, Request, Response

from app.api.forward_openai import forward_openai_request
from app.utils.logger import relay_log as logger

router = APIRouter(prefix="/v1", tags=["files"])


@router.get("/files")
async def list_files(request: Request) -> Response:
    """
    GET /v1/files
    Upstream: list files
    """
    logger.info("→ [files] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.post("/files")
async def create_file(request: Request) -> Response:
    """
    POST /v1/files
    Upstream expects multipart/form-data (file + purpose).
    We forward as-is.
    """
    logger.info("→ [files] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.get("/files/{file_id}")
async def retrieve_file(file_id: str, request: Request) -> Response:
    """
    GET /v1/files/{file_id}
    Upstream: retrieve file metadata
    """
    logger.info("→ [files] %s %s (file_id=%s)", request.method, request.url.path, file_id)
    return await forward_openai_request(request)


@router.delete("/files/{file_id}")
async def delete_file(file_id: str, request: Request) -> Response:
    """
    DELETE /v1/files/{file_id}
    Upstream: delete file
    """
    logger.info("→ [files] %s %s (file_id=%s)", request.method, request.url.path, file_id)
    return await forward_openai_request(request)


@router.get("/files/{file_id}/content")
async def retrieve_file_content_get(file_id: str, request: Request) -> Response:
    """
    GET /v1/files/{file_id}/content
    Upstream: retrieve file content (binary)
    """
    logger.info("→ [files] %s %s (file_id=%s)", request.method, request.url.path, file_id)
    return await forward_openai_request(request)


@router.head("/files/{file_id}/content", include_in_schema=False)
async def retrieve_file_content_head(file_id: str, request: Request) -> Response:
    """
    HEAD /v1/files/{file_id}/content

    HEAD is useful for clients, but it is not required for Actions/docs.
    We exclude it from OpenAPI to avoid duplicate operationId warnings.
    """
    logger.info("→ [files] %s %s (file_id=%s)", request.method, request.url.path, file_id)
    return await forward_openai_request(request)


@router.api_route(
    "/files/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"],
    include_in_schema=False,
)
async def files_passthrough(path: str, request: Request) -> Response:
    """
    Catch-all passthrough for future /v1/files/* endpoints.

    Kept out of OpenAPI to avoid operationId collisions and to keep
    the schema Actions-friendly.
    """
    logger.info("→ [files/*] %s %s (subpath=%s)", request.method, request.url.path, path)
    return await forward_openai_request(request)
```

## FILE: app/routes/health.py @ 4a039730f9a85ddb91f1a6f031321c2d232c27e1
```
# app/routes/health.py
from __future__ import annotations

import platform
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter

from app.core.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


def _safe_get(settings: Any, *names: str, default: Any = None) -> Any:
    for name in names:
        if hasattr(settings, name):
            val = getattr(settings, name)
            if val is not None:
                return val
    return default


def _base_status() -> Dict[str, Any]:
    s = get_settings()
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": _safe_get(s, "relay_name", "RELAY_NAME", default="chatgpt-team-relay"),
        "environment": _safe_get(s, "environment", "ENVIRONMENT", default="unknown"),
        "version": _safe_get(s, "version", "BIFL_VERSION", default="unknown"),
        "default_model": _safe_get(s, "default_model", "DEFAULT_MODEL", default=None),
        "realtime_model": _safe_get(s, "realtime_model", "REALTIME_MODEL", default=None),
        "openai_base_url": str(
            _safe_get(s, "openai_base_url", "OPENAI_API_BASE", default="https://api.openai.com/v1")
        ),
        # Never hard-crash health on config drift:
        "python_version": _safe_get(s, "PYTHON_VERSION", default=platform.python_version()),
    }


@router.get("/health")
async def health_root() -> Dict[str, Any]:
    return _base_status()


@router.get("/v1/health")
async def health_v1() -> Dict[str, Any]:
    return _base_status()
```

## FILE: app/routes/images.py @ 4a039730f9a85ddb91f1a6f031321c2d232c27e1
```
# app/routes/images.py

from __future__ import annotations

from fastapi import APIRouter, Request, Response

from app.api.forward_openai import forward_openai_request
from app.utils.logger import relay_log as logger

router = APIRouter(
    prefix="/v1",
    tags=["images"],
)


@router.post("/images/generations")
@router.post("/images")
async def create_image(request: Request) -> Response:
    """
    Image generation passthrough.

    Covers:
      - POST /v1/images/generations
      - POST /v1/images

    Tests:
      - test_image_generations_forward

    They assert:
      * HTTP 200
      * JSON body matches the stub from `forward_spy`
        (echo_path == "/v1/images/generations", echo_method == "POST")
    """
    logger.info("→ [images] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.post("/images/edits")
async def edit_image(request: Request) -> Response:
    """
    Image edits passthrough.

    This is used by:
      - test_image_edits_forward

    The test stubs the upstream endpoint:
      POST https://api.openai.com/v1/images/edits

    Our job is simply to forward the request and return whatever
    upstream sends (status code + JSON body).
    """
    logger.info("→ [images] %s %s (edits)", request.method, request.url.path)
    return await forward_openai_request(request)
```

## FILE: app/routes/models.py @ 4a039730f9a85ddb91f1a6f031321c2d232c27e1
```
# app/routes/models.py

from __future__ import annotations

from fastapi import APIRouter

from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# This router is mounted with prefix "/v1/models" in app.main
router = APIRouter(prefix="/v1/models", tags=["models"])


@router.get("")
async def list_models() -> dict:
    """
    Minimal, local implementation of GET /v1/models.

    For local development & integration tests we don't need to hit OpenAI.
    We just return a list with at least one model: settings.DEFAULT_MODEL.
    """
    default_id = settings.DEFAULT_MODEL

    logger.info("→ [models] local list /v1/models (default=%s)", default_id)

    return {
        "object": "list",
        "data": [
            {
                "object": "model",
                "id": default_id,
                "owned_by": "system",
            }
        ],
    }


@router.get("/{model_id}")
async def retrieve_model(model_id: str) -> dict:
    """
    Minimal, local implementation of GET /v1/models/{id}.

    Always returns a simple model object; tests only check:
      - body["object"] == "model"
      - body["id"] == requested id
    """
    logger.info("→ [models] local retrieve /v1/models/%s", model_id)

    return {
        "object": "model",
        "id": model_id,
        "owned_by": "system",
    }
```

## FILE: app/routes/proxy.py @ 4a039730f9a85ddb91f1a6f031321c2d232c27e1
```
from __future__ import annotations

import re
from typing import Any, Dict, Optional, Set, Tuple

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import AliasChoices, BaseModel, ConfigDict, Field, model_validator

from app.api.forward_openai import forward_openai_method_path

router = APIRouter(prefix="/v1", tags=["proxy"])


class ProxyRequest(BaseModel):
    """
    Action-friendly proxy envelope (Option A).

    NOTE:
    - We intentionally do NOT use a field named `json`, because it shadows
      BaseModel.json() and triggers Pydantic warnings.
    - For backward compatibility, we still ACCEPT an input key named "json"
      as an alias to `body`.
    """

    model_config = ConfigDict(extra="forbid")

    method: str = Field(..., description="HTTP method: GET, POST, PUT, PATCH, DELETE")
    path: str = Field(..., description="Upstream OpenAI path, e.g. /v1/responses")

    # Accept multiple common spellings (client convenience).
    query: Optional[Dict[str, Any]] = Field(
        default=None,
        validation_alias=AliasChoices("query", "params", "query_params"),
        description="Query parameters (object/dict)",
    )

    # Back-compat: accept {"json": {...}} from older clients/examples
    body: Optional[Any] = Field(
        default=None,
        validation_alias=AliasChoices("body", "json", "json_body"),
        description="JSON body for POST/PUT/PATCH requests",
    )

    @model_validator(mode="after")
    def _avoid_empty_json_body_parse_errors(self) -> "ProxyRequest":
        """
        Some clients omit the body entirely for POST-like methods.
        Defaulting to {} gives a consistent upstream behavior (400 w/ details)
        instead of 'empty body' edge cases.
        """
        m = (self.method or "").strip().upper()
        if m in {"POST", "PUT", "PATCH"} and self.body is None:
            self.body = {}
        return self


_ALLOWED_METHODS: Set[str] = {"GET", "POST", "PUT", "PATCH", "DELETE"}

# Block higher-risk or non-Action-friendly families by prefix.
_BLOCKED_PREFIXES: Tuple[str, ...] = (
    "/v1/admin",
    "/v1/webhooks",
    "/v1/moderations",
    "/v1/realtime",   # websocket family (not Actions-friendly)
    "/v1/uploads",    # multipart/resumable
    "/v1/audio",      # often multipart/binary
)

# Block direct recursion and local-only helpers
_BLOCKED_PATHS: Set[str] = {
    "/v1/proxy",
    "/v1/responses:stream",
}

# Block binary-ish suffixes (Actions are JSON-first)
_BLOCKED_SUFFIXES: Tuple[str, ...] = (
    "/content",
    "/results",
)

# Multipart endpoints that should not be routed via JSON envelope
_BLOCKED_METHOD_PATH_REGEX: Set[Tuple[str, re.Pattern[str]]] = {
    ("POST", re.compile(r"^/v1/files$")),
    ("POST", re.compile(r"^/v1/images/(edits|variations)$")),
    ("POST", re.compile(r"^/v1/videos$")),  # per API ref, create video is multipart/form-data
}

# Allowlist: (methods, regex)
_ALLOWLIST: Tuple[Tuple[Set[str], re.Pattern[str]], ...] = (
    # ---- Responses (JSON) ----
    ({"POST"}, re.compile(r"^/v1/responses$")),
    ({"POST"}, re.compile(r"^/v1/responses/compact$")),
    ({"GET"}, re.compile(r"^/v1/responses/[A-Za-z0-9_-]+$")),
    ({"DELETE"}, re.compile(r"^/v1/responses/[A-Za-z0-9_-]+$")),
    ({"POST"}, re.compile(r"^/v1/responses/[A-Za-z0-9_-]+/cancel$")),
    ({"GET"}, re.compile(r"^/v1/responses/[A-Za-z0-9_-]+/input_items$")),
    ({"POST"}, re.compile(r"^/v1/responses/input_tokens$")),

    # ---- Embeddings (JSON) ----
    ({"POST"}, re.compile(r"^/v1/embeddings$")),

    # ---- Models (JSON) ----
    ({"GET"}, re.compile(r"^/v1/models$")),
    ({"GET"}, re.compile(r"^/v1/models/[^/]+$")),

    # ---- Images (JSON only: generations) ----
    ({"POST"}, re.compile(r"^/v1/images/generations$")),
    ({"POST"}, re.compile(r"^/v1/images$")),

    # ---- Videos (metadata only via proxy; content is binary, create is multipart) ----
    ({"GET"}, re.compile(r"^/v1/videos$")),
    ({"GET"}, re.compile(r"^/v1/videos/[^/]+$")),
    ({"DELETE"}, re.compile(r"^/v1/videos/[^/]+$")),

    # ---- Vector Stores (JSON) ----
    ({"GET"}, re.compile(r"^/v1/vector_stores$")),
    ({"POST"}, re.compile(r"^/v1/vector_stores$")),
    ({"GET"}, re.compile(r"^/v1/vector_stores/[^/]+$")),
    ({"POST"}, re.compile(r"^/v1/vector_stores/[^/]+$")),
    ({"DELETE"}, re.compile(r"^/v1/vector_stores/[^/]+$")),
    ({"POST"}, re.compile(r"^/v1/vector_stores/[^/]+/search$")),

    # vector store files
    ({"POST"}, re.compile(r"^/v1/vector_stores/[^/]+/files$")),
    ({"GET"}, re.compile(r"^/v1/vector_stores/[^/]+/files$")),
    ({"GET"}, re.compile(r"^/v1/vector_stores/[^/]+/files/[^/]+$")),
    ({"POST"}, re.compile(r"^/v1/vector_stores/[^/]+/files/[^/]+$")),
    ({"DELETE"}, re.compile(r"^/v1/vector_stores/[^/]+/files/[^/]+$")),

    # vector store file batches
    ({"POST"}, re.compile(r"^/v1/vector_stores/[^/]+/file_batches$")),
    ({"GET"}, re.compile(r"^/v1/vector_stores/[^/]+/file_batches/[^/]+$")),
    ({"POST"}, re.compile(r"^/v1/vector_stores/[^/]+/file_batches/[^/]+/cancel$")),
    ({"GET"}, re.compile(r"^/v1/vector_stores/[^/]+/file_batches/[^/]+/files$")),

    # ---- Containers (JSON control plane only) ----
    ({"GET"}, re.compile(r"^/v1/containers$")),
    ({"POST"}, re.compile(r"^/v1/containers$")),
    ({"GET"}, re.compile(r"^/v1/containers/[^/]+$")),
    ({"DELETE"}, re.compile(r"^/v1/containers/[^/]+$")),

    # ---- Conversations (JSON) ----
    ({"POST"}, re.compile(r"^/v1/conversations$")),
    ({"GET"}, re.compile(r"^/v1/conversations/[^/]+$")),
    ({"POST"}, re.compile(r"^/v1/conversations/[^/]+$")),
    ({"DELETE"}, re.compile(r"^/v1/conversations/[^/]+$")),

    # ---- Files (JSON metadata only; content is binary; create is multipart) ----
    ({"GET"}, re.compile(r"^/v1/files$")),
    ({"GET"}, re.compile(r"^/v1/files/[A-Za-z0-9_-]+$")),
    ({"DELETE"}, re.compile(r"^/v1/files/[A-Za-z0-9_-]+$")),
)


def _normalize_path(path: str) -> str:
    p = (path or "").strip()

    if not p:
        raise HTTPException(status_code=400, detail="path is required")

    # Disallow full URLs; only allow API paths.
    if "://" in p or p.lower().startswith("http"):
        raise HTTPException(status_code=400, detail="path must be an OpenAI API path, not a URL")

    # Disallow embedded query strings (use `query` field).
    if "?" in p:
        raise HTTPException(status_code=400, detail="path must not include '?'; use `query` field")

    if not p.startswith("/"):
        p = "/" + p

    # Ensure /v1 prefix
    if p.startswith("/v1"):
        normalized = p
    elif p.startswith("v1/"):
        normalized = "/" + p
    else:
        normalized = "/v1" + p

    # Collapse accidental double slashes
    while "//" in normalized:
        normalized = normalized.replace("//", "/")

    return normalized


def _blocked_reason(method: str, path: str, body: Any) -> Optional[str]:
    # No streaming via proxy envelope
    if isinstance(body, dict) and body.get("stream") is True:
        return "stream=true is not allowed via /v1/proxy (use explicit streaming route)"

    # Block weird colon paths like /v1/responses:stream
    if ":" in path:
        return "':' paths are not allowed via /v1/proxy"

    # Basic traversal guards
    if ".." in path or "#" in path:
        return "path contains illegal sequences"
    if any(ch.isspace() for ch in path):
        return "path must not contain whitespace"

    if path in _BLOCKED_PATHS:
        return "path is blocked"

    for prefix in _BLOCKED_PREFIXES:
        if path.startswith(prefix):
            return f"blocked prefix: {prefix}"

    for suffix in _BLOCKED_SUFFIXES:
        if path.endswith(suffix):
            return f"blocked suffix: {suffix}"

    for (m, rx) in _BLOCKED_METHOD_PATH_REGEX:
        if method == m and rx.match(path):
            return "multipart endpoint blocked via /v1/proxy"

    return None


def _is_allowlisted(method: str, path: str) -> bool:
    for methods, rx in _ALLOWLIST:
        if method in methods and rx.match(path):
            return True
    return False


@router.post("/proxy")
async def proxy(call: ProxyRequest, request: Request) -> Response:
    method = (call.method or "").strip().upper()
    if method not in _ALLOWED_METHODS:
        raise HTTPException(status_code=400, detail=f"Unsupported method: {call.method}")

    path = _normalize_path(call.path)

    reason = _blocked_reason(method, path, call.body)
    if reason:
        raise HTTPException(status_code=403, detail={"error": reason})

    if not _is_allowlisted(method, path):
        raise HTTPException(status_code=403, detail="method/path not allowlisted for /v1/proxy")

    return await forward_openai_method_path(
        method=method,
        path=path,
        query=call.query,
        json_body=call.body,
        inbound_headers=request.headers,
    )
```

## FILE: app/routes/realtime.py @ 4a039730f9a85ddb91f1a6f031321c2d232c27e1
```
# app/routes/realtime.py

from __future__ import annotations

import asyncio
import json
import os
from typing import Any, Dict, Optional, Tuple

import httpx
from fastapi import APIRouter, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from websockets import connect as ws_connect  # type: ignore
from websockets.exceptions import ConnectionClosed  # type: ignore

from app.utils.logger import relay_log as logger

OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com").rstrip("/")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_REALTIME_BETA = os.getenv("OPENAI_REALTIME_BETA", "realtime=v1")
PROXY_TIMEOUT = float(os.getenv("PROXY_TIMEOUT", os.getenv("RELAY_TIMEOUT", "120")))
DEFAULT_REALTIME_MODEL = os.getenv("REALTIME_MODEL", "gpt-4.1-mini")

router = APIRouter(
    prefix="/v1",
    tags=["realtime"],
)


def _build_headers(request: Request | None = None) -> Dict[str, str]:
    if not OPENAI_API_KEY:
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "message": "OPENAI_API_KEY is not configured for Realtime sessions",
                    "type": "config_error",
                    "code": "no_api_key",
                }
            },
        )

    headers: Dict[str, str] = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    incoming_beta = request.headers.get("OpenAI-Beta") if request else None
    beta = incoming_beta or OPENAI_REALTIME_BETA
    if beta:
        headers["OpenAI-Beta"] = beta

    return headers


async def _post_realtime_sessions(
    request: Request,
    body: Optional[Dict[str, Any]] = None,
) -> Tuple[int, Dict[str, Any]]:
    """
    Helper for POST /v1/realtime/sessions
    """
    url = f"{OPENAI_API_BASE}/v1/realtime/sessions"
    headers = _build_headers(request)
    timeout = httpx.Timeout(PROXY_TIMEOUT)

    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            resp = await client.post(url, headers=headers, json=body or {})
        except httpx.RequestError as exc:
            logger.error("Error calling OpenAI Realtime sessions: %r", exc)
            raise HTTPException(
                status_code=502,
                detail={
                    "error": {
                        "message": "Error calling OpenAI Realtime sessions",
                        "type": "server_error",
                        "code": "upstream_request_error",
                        "extra": {"exception": str(exc)},
                    }
                },
            ) from exc

    try:
        data = resp.json()
    except json.JSONDecodeError:
        data = {"raw": resp.text}

    return resp.status_code, data


@router.post("/realtime/sessions")
async def create_realtime_session(request: Request) -> JSONResponse:
    """
    POST /v1/realtime/sessions – create a Realtime session descriptor.

    If the client omits `model`, we default to REALTIME_MODEL.
    """
    try:
        payload = await request.json()
    except Exception:
        payload = {}

    if not isinstance(payload, dict):
        payload = {}

    payload.setdefault("model", DEFAULT_REALTIME_MODEL)

    status_code, data = await _post_realtime_sessions(request, payload)
    return JSONResponse(status_code=status_code, content=data)


def _build_ws_base() -> str:
    """
    Convert OPENAI_API_BASE (http/https) into ws/wss base for Realtime WS.
    """
    if OPENAI_API_BASE.startswith("https://"):
        return "wss://" + OPENAI_API_BASE[len("https://") :]
    if OPENAI_API_BASE.startswith("http://"):
        return "ws://" + OPENAI_API_BASE[len("http://") :]
    # Fallback: assume already ws/wss
    return OPENAI_API_BASE


@router.websocket("/realtime/ws")
async def realtime_ws(websocket: WebSocket) -> None:
    """
    WebSocket proxy between client and OpenAI Realtime WS.

    Client connects to:
      ws(s)://relay-host/v1/realtime/ws?model=.&session_id=.

    Relay connects to:
      wss://api.openai.com/v1/realtime?model=.&session_id=.
    """
    await websocket.accept(subprotocol="openai-realtime-v1")

    model = websocket.query_params.get("model") or DEFAULT_REALTIME_MODEL
    session_id = websocket.query_params.get("session_id")

    ws_base = _build_ws_base()
    url = f"{ws_base}/v1/realtime?model={model}"
    if session_id:
        url += f"&session_id={session_id}"

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "OpenAI-Beta": OPENAI_REALTIME_BETA,
    }

    try:
        async with ws_connect(
            url,
            extra_headers=headers,
            subprotocols=["openai-realtime-v1"],
        ) as upstream_ws:

            async def _client_to_openai() -> None:
                try:
                    while True:
                        msg = await websocket.receive()
                        if msg["type"] == "websocket.disconnect":
                            await upstream_ws.close()
                            break
                        if msg.get("text") is not None:
                            await upstream_ws.send(msg["text"])
                        elif msg.get("bytes") is not None:
                            await upstream_ws.send(msg["bytes"])
                except WebSocketDisconnect:
                    await upstream_ws.close()
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Client->OpenAI WS error: %r", exc)
                    await upstream_ws.close()

            async def _openai_to_client() -> None:
                try:
                    async for message in upstream_ws:
                        if isinstance(message, bytes):
                            await websocket.send_bytes(message)
                        else:
                            await websocket.send_text(message)
                except ConnectionClosed:
                    await websocket.close()
                except Exception as exc:  # noqa: BLE001
                    logger.warning("OpenAI->Client WS error: %r", exc)
                    await websocket.close()

            await asyncio.gather(_client_to_openai(), _openai_to_client())

    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to establish WS to OpenAI: %r", exc)
        await websocket.close()
```

## FILE: app/routes/register_routes.py @ 4a039730f9a85ddb91f1a6f031321c2d232c27e1
```
# app/routes/register_routes.py

from __future__ import annotations

from typing import Protocol

from fastapi import APIRouter

from . import (
    actions,
    batches,
    containers,
    conversations,
    embeddings,
    files,
    health,
    images,
    models,
    proxy,
    realtime,
    responses,
    uploads,
    vector_stores,
    videos,
)


class _RouterLike(Protocol):
    """Structural protocol for FastAPI / APIRouter (anything with include_router)."""

    def include_router(self, router: APIRouter, **kwargs) -> None:  # pragma: no cover
        ...


def register_routes(app: _RouterLike) -> None:
    """Register all route families on the given FastAPI app or APIRouter.

    Ordering matters: mount specific routers first and the generic `/v1/proxy`
    last so explicit routes always win.
    """

    # Health is special: exposes both `/health` and `/v1/health`
    app.include_router(health.router)

    # Relay diagnostics / metadata for Actions
    app.include_router(actions.router)

    # Core OpenAI resource families
    app.include_router(responses.router)  # /v1/responses
    app.include_router(embeddings.router)  # /v1/embeddings
    app.include_router(images.router)  # /v1/images
    app.include_router(videos.router)  # /v1/videos
    app.include_router(models.router)  # /v1/models (local stub)

    # Files & uploads (multipart, binary content)
    app.include_router(files.router)  # /v1/files
    app.include_router(uploads.router)  # /v1/uploads
    app.include_router(vector_stores.router)  # /v1/vector_stores (+ /vector_stores)

    # Higher-level surfaces
    app.include_router(conversations.router)  # /v1/conversations
    app.include_router(containers.router)  # /v1/containers
    app.include_router(batches.router)  # /v1/batches
    app.include_router(realtime.router)  # /v1/realtime (HTTP + WS)

    # Generic allowlisted proxy LAST
    app.include_router(proxy.router)  # /v1/proxy


def register_all_routes(app: _RouterLike) -> None:
    """Backwards compatibility alias (older main.py imports)."""
    register_routes(app)
```

## FILE: app/routes/responses.py @ 4a039730f9a85ddb91f1a6f031321c2d232c27e1
```
from __future__ import annotations

import asyncio
import json
from typing import Any, Dict

import httpx
from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import StreamingResponse

from app.api.forward_openai import (
    build_upstream_url,
    forward_openai_request,
    forward_responses_create,
)
from app.api.sse import create_sse_stream
from app.core.config import get_settings
from app.core.http_client import get_async_httpx_client

router = APIRouter(prefix="/v1", tags=["responses"])


@router.post("/responses")
async def create_response(request: Request) -> Response:
    """
    POST /v1/responses
    - Supports JSON payload
    - If payload has {"stream": true}, we stream SSE from upstream.
    """
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    # If stream requested, proxy SSE stream directly.
    if body.get("stream") is True:
        settings = get_settings()
        url = build_upstream_url("/v1/responses")

        headers = {
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json",
        }
        if settings.openai_organization:
            headers["OpenAI-Organization"] = settings.openai_organization
        if settings.openai_project:
            headers["OpenAI-Project"] = settings.openai_project
        if settings.openai_beta:
            headers["OpenAI-Beta"] = settings.openai_beta

        data = json.dumps(body).encode("utf-8")
        client = get_async_httpx_client()

        async def event_generator():
            async with client.stream(
                "POST",
                url,
                headers=headers,
                content=data,
                timeout=settings.proxy_timeout_seconds,
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if line:
                        yield line + "\n"

        return StreamingResponse(
            create_sse_stream(event_generator()),
            media_type="text/event-stream",
        )

    # Non-streaming: use SDK (typed) and return JSON.
    result = await forward_responses_create(body)
    return Response(
        content=json.dumps(result),
        media_type="application/json",
    )


@router.post("/responses/compact")
async def create_response_compact(request: Request) -> Response:
    """
    POST /v1/responses/compact
    - convenience wrapper that can keep payload minimal on the client side
    """
    body = await request.json()
    body["metadata"] = body.get("metadata", {})
    body["metadata"]["compact"] = True
    result = await forward_responses_create(body)
    return Response(
        content=json.dumps(result),
        media_type="application/json",
    )


# --- Missing lifecycle endpoints (now added) ---


@router.get("/responses/{response_id}")
async def get_response(response_id: str, request: Request) -> Response:
    return await forward_openai_request(request)


@router.delete("/responses/{response_id}")
async def delete_response(response_id: str, request: Request) -> Response:
    return await forward_openai_request(request)


@router.post("/responses/{response_id}/cancel")
async def cancel_response(response_id: str, request: Request) -> Response:
    return await forward_openai_request(request)


@router.get("/responses/{response_id}/input_items")
async def get_response_input_items(response_id: str, request: Request) -> Response:
    return await forward_openai_request(request)


@router.post("/responses/input_tokens")
async def get_input_token_counts(request: Request) -> Response:
    """
    POST /v1/responses/input_tokens
    (This is a top-level endpoint in the OpenAI API reference.)
    """
    return await forward_openai_request(request)


# Catch-all passthrough for future /v1/responses/* subroutes.
@router.api_route(
    "/responses/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    include_in_schema=False,
)
async def responses_passthrough(path: str, request: Request) -> Response:
    return await forward_openai_request(request)


# --- Simple SSE helper endpoint used by some clients/tests ---


@router.get("/responses:stream")
async def responses_stream() -> Response:
    """
    Deprecated-ish helper. Kept for compatibility.
    """
    async def gen():
        for i in range(3):
            yield f"data: ping {i}\n\n"
            await asyncio.sleep(0.1)

    return StreamingResponse(gen(), media_type="text/event-stream")
```

## FILE: app/routes/uploads.py @ 4a039730f9a85ddb91f1a6f031321c2d232c27e1
```
# app/routes/uploads.py

from __future__ import annotations

from fastapi import APIRouter, Request, Response

from app.api.forward_openai import forward_openai_request
from app.utils.logger import relay_log as logger

router = APIRouter(prefix="/v1", tags=["uploads"])


@router.post("/uploads")
async def create_upload(request: Request) -> Response:
    """
    POST /v1/uploads

    Upstream: Creates an intermediate Upload; once completed, it yields a File.
    (OpenAI API Reference: Uploads)
    """
    logger.info("→ [uploads] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.post("/uploads/{upload_id}/parts")
async def add_upload_part(upload_id: str, request: Request) -> Response:
    """
    POST /v1/uploads/{upload_id}/parts

    Upstream expects multipart/form-data with a required 'data' file field.
    We forward as-is.
    """
    logger.info("→ [uploads] %s %s (upload_id=%s)", request.method, request.url.path, upload_id)
    return await forward_openai_request(request)


@router.post("/uploads/{upload_id}/complete")
async def complete_upload(upload_id: str, request: Request) -> Response:
    """
    POST /v1/uploads/{upload_id}/complete

    Upstream expects JSON body:
      {"part_ids": ["part_...","part_..."], "md5": "..."}  # md5 optional
    """
    logger.info("→ [uploads] %s %s (complete upload_id=%s)", request.method, request.url.path, upload_id)
    return await forward_openai_request(request)


@router.post("/uploads/{upload_id}/cancel")
async def cancel_upload(upload_id: str, request: Request) -> Response:
    """
    POST /v1/uploads/{upload_id}/cancel
    """
    logger.info("→ [uploads] %s %s (cancel upload_id=%s)", request.method, request.url.path, upload_id)
    return await forward_openai_request(request)


@router.api_route(
    "/uploads/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"],
    include_in_schema=False,
)
async def uploads_passthrough(path: str, request: Request) -> Response:
    """
    Catch-all passthrough for future /v1/uploads/* endpoints.
    """
    logger.info("→ [uploads/*] %s %s (subpath=%s)", request.method, request.url.path, path)
    return await forward_openai_request(request)
```

## FILE: app/routes/vector_stores.py @ 4a039730f9a85ddb91f1a6f031321c2d232c27e1
```
from __future__ import annotations

from fastapi import APIRouter, Request, Response

from app.api.forward_openai import forward_openai_request

router = APIRouter(tags=["vector_stores"])


async def _forward(request: Request) -> Response:
    return await forward_openai_request(request)


# ---- /v1/vector_stores (split methods to avoid duplicate operationId) ----
@router.get("/v1/vector_stores")
async def vector_stores_root_get(request: Request) -> Response:
    return await _forward(request)


@router.post("/v1/vector_stores")
async def vector_stores_root_post(request: Request) -> Response:
    return await _forward(request)


@router.put("/v1/vector_stores")
async def vector_stores_root_put(request: Request) -> Response:
    return await _forward(request)


@router.patch("/v1/vector_stores")
async def vector_stores_root_patch(request: Request) -> Response:
    return await _forward(request)


@router.delete("/v1/vector_stores")
async def vector_stores_root_delete(request: Request) -> Response:
    return await _forward(request)


# ---- /v1/vector_stores/{path:path} (split methods to avoid duplicate operationId) ----
@router.get("/v1/vector_stores/{path:path}")
async def vector_stores_subpaths_get(path: str, request: Request) -> Response:
    return await _forward(request)


@router.post("/v1/vector_stores/{path:path}")
async def vector_stores_subpaths_post(path: str, request: Request) -> Response:
    return await _forward(request)


@router.put("/v1/vector_stores/{path:path}")
async def vector_stores_subpaths_put(path: str, request: Request) -> Response:
    return await _forward(request)


@router.patch("/v1/vector_stores/{path:path}")
async def vector_stores_subpaths_patch(path: str, request: Request) -> Response:
    return await _forward(request)


@router.delete("/v1/vector_stores/{path:path}")
async def vector_stores_subpaths_delete(path: str, request: Request) -> Response:
    return await _forward(request)


# ---- Alias paths (kept hidden from OpenAPI) ----
_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE"]


@router.api_route("/vector_stores", methods=_METHODS, include_in_schema=False)
async def vector_stores_root_alias(request: Request) -> Response:
    return await _forward(request)


@router.api_route("/vector_stores/{path:path}", methods=_METHODS, include_in_schema=False)
async def vector_stores_subpaths_alias(path: str, request: Request) -> Response:
    return await _forward(request)
```

## FILE: app/routes/videos.py @ 4a039730f9a85ddb91f1a6f031321c2d232c27e1
```
from __future__ import annotations

from fastapi import APIRouter, Request

from app.api.forward_openai import forward_openai_method_path, forward_openai_request
from app.utils.logger import info

router = APIRouter(prefix="/v1", tags=["videos"])


# --- Canonical Videos API (per OpenAI API reference) ---
#
# POST   /v1/videos                       -> create a video generation job (may be multipart)
# POST   /v1/videos/{video_id}/remix       -> remix an existing video
# GET    /v1/videos                       -> list videos
# GET    /v1/videos/{video_id}            -> retrieve a video job
# DELETE /v1/videos/{video_id}            -> delete a video job
# GET    /v1/videos/{video_id}/content    -> download generated content (binary)
#
# We implement the main paths explicitly (for clean OpenAPI + clarity), and keep a
# hidden catch-all for forward-compat endpoints that may appear later.


@router.post("/videos")
async def create_video(request: Request):
    """Create a new video generation job (JSON or multipart/form-data)."""
    info("→ [videos.create] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.post("/videos/generations", deprecated=True)
async def create_video_legacy_generations(request: Request):
    """Legacy alias: historically `/v1/videos/generations` in older relays.

    The current OpenAI API uses `POST /v1/videos`. We forward this endpoint to
    the canonical path for compatibility.
    """
    info("→ [videos.legacy_generations] %s %s", request.method, request.url.path)
    return await forward_openai_method_path("POST", "/v1/videos", request)


@router.post("/videos/{video_id}/remix")
async def remix_video(video_id: str, request: Request):
    """Create a remix of an existing video job."""
    info("→ [videos.remix] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.get("/videos")
async def list_videos(request: Request):
    """List video jobs."""
    info("→ [videos.list] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.get("/videos/{video_id}")
async def retrieve_video(video_id: str, request: Request):
    """Retrieve a single video job."""
    info("→ [videos.retrieve] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.delete("/videos/{video_id}")
async def delete_video(video_id: str, request: Request):
    """Delete a single video job."""
    info("→ [videos.delete] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.get("/videos/{video_id}/content")
async def download_video_content(video_id: str, request: Request):
    """Download generated content (binary) for a video job."""
    info("→ [videos.content] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


# Forward-compat / extra endpoints (hidden from OpenAPI schema)
@router.api_route(
    "/videos/{path:path}",
    methods=["GET", "POST", "DELETE", "PATCH", "PUT", "HEAD", "OPTIONS"],
    include_in_schema=False,
)
async def videos_passthrough(path: str, request: Request):
    info("→ [videos/*] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)
```

## FILE: app/utils/__init__.py @ 4a039730f9a85ddb91f1a6f031321c2d232c27e1
```
```

## FILE: app/utils/authy.py @ 4a039730f9a85ddb91f1a6f031321c2d232c27e1
```
# app/utils/authy.py

from __future__ import annotations

import hmac
from typing import Optional

from fastapi import HTTPException, status

from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


def _get_expected_key() -> str:
    """
    Return the configured relay key as a plain string.

    Prefer settings.RELAY_KEY, but keep a fallback to RELAY_AUTH_TOKEN
    for compatibility with older configs.
    """
    if getattr(settings, "RELAY_KEY", None):
        return settings.RELAY_KEY

    # Legacy / fallback name
    token = getattr(settings, "RELAY_AUTH_TOKEN", None)
    return token or ""


def _extract_bearer_token(auth_header: Optional[str]) -> Optional[str]:
    """
    Parse an Authorization header of the form 'Bearer <token>'.

    Returns the token string, or None if the header is missing.

    Raises HTTPException(401) if the header is present but malformed.
    """
    if not auth_header:
        return None

    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Relay requires 'Bearer' Authorization scheme",
        )

    token = parts[1].strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing relay key",
        )

    return token


def check_relay_key(
    auth_header: Optional[str],
    x_relay_key: Optional[str],
) -> None:
    """
    Validate incoming relay key.

    Priority:
      1. X-Relay-Key header (used by relay_e2e_raw.py / tools)
      2. Authorization: Bearer <token> (used by SDK-style clients)

    If RELAY_AUTH_ENABLED is False, this is a no-op.

    On failure, raises HTTPException(status_code=..., detail="<string>").
    """
    # If auth is disabled, skip entirely
    if not getattr(settings, "RELAY_AUTH_ENABLED", False):
        return

    # Prefer explicit X-Relay-Key when present
    token: Optional[str] = None
    if x_relay_key:
        token = x_relay_key.strip()
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing relay key",
            )
    else:
        # Fall back to Authorization header
        token = _extract_bearer_token(auth_header)

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing relay key",
        )

    expected = _get_expected_key().encode("utf-8")
    provided = token.encode("utf-8")

    if not expected:
        # Config bug; log and fail closed
        logger.error(
            "Relay auth misconfigured: RELAY_KEY is empty when auth is enabled",
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Relay auth misconfigured",
        )

    if not hmac.compare_digest(expected, provided):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid relay key",
        )
```

## FILE: app/utils/error_handler.py @ 4a039730f9a85ddb91f1a6f031321c2d232c27e1
```
# app/utils/error_handler.py

from __future__ import annotations

from typing import Any, Optional, Type

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from openai._exceptions import OpenAIError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import ClientDisconnect

from app.utils.logger import get_logger

logger = get_logger(__name__)

# Non-standard but widely used by proxies (e.g., nginx) to signal "Client Closed Request".
CLIENT_CLOSED_REQUEST_STATUS = 499


def _base_error_payload(
    message: str,
    status: int,
    code: Optional[str] = None,
) -> dict[str, Any]:
    return {
        "error": {
            "message": message,
            "type": "relay_error",
            "param": None,
            "code": code,
        },
        "status": status,
    }


# ExceptionGroup exists in Python 3.11+
try:
    ExceptionGroupType: Optional[Type[BaseException]] = ExceptionGroup  # type: ignore[name-defined]
except NameError:  # pragma: no cover
    ExceptionGroupType = None


def _is_client_disconnect(exc: BaseException) -> bool:
    """
    Return True if:
      - exc is ClientDisconnect, OR
      - exc is an ExceptionGroup where *every* inner exception is a ClientDisconnect.
    """
    if isinstance(exc, ClientDisconnect):
        return True

    if ExceptionGroupType is not None and isinstance(exc, ExceptionGroupType):
        try:
            # ExceptionGroup exposes `.exceptions` (tuple of underlying exceptions)
            inner = exc.exceptions  # type: ignore[attr-defined]
            return all(_is_client_disconnect(e) for e in inner)
        except Exception:
            return False

    return False


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        logger.warning("HTTP error", extra={"status_code": exc.status_code, "detail": exc.detail})
        return JSONResponse(
            status_code=exc.status_code,
            content=_base_error_payload(str(exc.detail), exc.status_code),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.warning("Validation error", extra={"errors": exc.errors()})
        return JSONResponse(
            status_code=422,
            content=_base_error_payload("Validation error", 422),
        )

    @app.exception_handler(OpenAIError)
    async def openai_exception_handler(request: Request, exc: OpenAIError):
        logger.error("OpenAI API error", extra={"error": str(exc)})
        return JSONResponse(
            status_code=502,
            content=_base_error_payload(f"Upstream OpenAI error: {exc}", 502),
        )

    @app.exception_handler(ClientDisconnect)
    async def client_disconnect_handler(request: Request, exc: ClientDisconnect):
        # Client closed connection mid-request. This is not a server bug; do not log as ERROR.
        logger.info(
            "Client disconnected",
            extra={"method": request.method, "path": request.url.path},
        )
        return JSONResponse(
            status_code=CLIENT_CLOSED_REQUEST_STATUS,
            content=_base_error_payload("Client disconnected", CLIENT_CLOSED_REQUEST_STATUS),
        )

    if ExceptionGroupType is not None:

        @app.exception_handler(ExceptionGroupType)  # type: ignore[arg-type]
        async def exception_group_handler(request: Request, exc: BaseException):
            # Starlette/AnyIO may wrap disconnects inside an ExceptionGroup.
            if _is_client_disconnect(exc):
                logger.info(
                    "Client disconnected (exception group)",
                    extra={"method": request.method, "path": request.url.path},
                )
                return JSONResponse(
                    status_code=CLIENT_CLOSED_REQUEST_STATUS,
                    content=_base_error_payload("Client disconnected", CLIENT_CLOSED_REQUEST_STATUS),
                )

            logger.exception("Unhandled exception group")
            return JSONResponse(
                status_code=500,
                content=_base_error_payload("Internal Server Error", 500),
            )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        # Defensive fallback: in case a disconnect slips through as a generic Exception.
        if _is_client_disconnect(exc):
            logger.info(
                "Client disconnected (caught by generic handler)",
                extra={"method": request.method, "path": request.url.path},
            )
            return JSONResponse(
                status_code=CLIENT_CLOSED_REQUEST_STATUS,
                content=_base_error_payload("Client disconnected", CLIENT_CLOSED_REQUEST_STATUS),
            )

        logger.exception("Unhandled server error")
        return JSONResponse(
            status_code=500,
            content=_base_error_payload("Internal Server Error", 500),
        )
```

## FILE: app/utils/http_client.py @ 4a039730f9a85ddb91f1a6f031321c2d232c27e1
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

## FILE: app/utils/logger.py @ 4a039730f9a85ddb91f1a6f031321c2d232c27e1
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

## BASELINE (tests/)

## FILE: tests/__init__.py @ 4a039730f9a85ddb91f1a6f031321c2d232c27e1
```
```

## FILE: tests/client.py @ 4a039730f9a85ddb91f1a6f031321c2d232c27e1
```
# tests/client.py

import os
from starlette.testclient import TestClient

# Ensure the app sees a test-friendly environment *before* it is imported.
os.environ.setdefault("APP_MODE", "test")
os.environ.setdefault("ENVIRONMENT", "test")

# You explicitly chose Option A: disable relay auth in tests.
# This makes RelayAuthMiddleware's check_relay_key() a no-op.
os.environ.setdefault("RELAY_AUTH_ENABLED", "false")

# Upstream base URL can stay default; override if you proxy:
os.environ.setdefault("OPENAI_API_BASE", "https://api.openai.com/v1")

from app.main import app  # noqa: E402  (import after env is set)


def _build_client() -> TestClient:
    client = TestClient(app)

    # Optional: if you ever want to test auth-enabled paths locally,
    # set RELAY_KEY in your environment and this will send an Authorization header.
    relay_key = os.getenv("RELAY_KEY")
    if relay_key:
        client.headers.update({"Authorization": f"Bearer {relay_key}"})

    return client


# Shared client instance used by all tests via the fixture in conftest.py
client: TestClient = _build_client()
```

## FILE: tests/conftest.py @ 4a039730f9a85ddb91f1a6f031321c2d232c27e1
```
# tests/conftest.py
from __future__ import annotations

import os
from typing import AsyncIterator

import httpx
import pytest
import pytest_asyncio

from app.main import app
from app.core.config import settings


@pytest_asyncio.fixture
async def async_client() -> AsyncIterator[httpx.AsyncClient]:
    """
    Shared async HTTP client that talks to the FastAPI app in-process via ASGI.

    - Uses httpx.ASGITransport so there is no real network involved.
    - Automatically sends Authorization: Bearer <RELAY_KEY or 'dummy'>,
      which matches how the OpenAI SDK talks to the relay in practice.
    """
    relay_key = os.getenv("RELAY_KEY", "dummy")

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
        headers={"Authorization": f"Bearer {relay_key}"},
        timeout=30.0,
    ) as client:
        yield client
```

## FILE: tests/test_local_e2e.py @ 4a039730f9a85ddb91f1a6f031321c2d232c27e1
```
# tests/test_local_e2e.py
from __future__ import annotations

import json

import httpx
import pytest

from app.core.config import settings

# All tests in this module are async
pytestmark = pytest.mark.asyncio


@pytest.mark.integration
async def test_health_endpoints_ok(async_client: httpx.AsyncClient) -> None:
    paths = ["/", "/health", "/v1/health"]

    for path in paths:
        resp = await async_client.get(path)
        assert resp.status_code == 200, f"{path} returned {resp.status_code}"

        body = resp.json()
        # Top-level sanity checks
        assert body.get("object") == "health"
        assert body.get("status") == "ok"
        assert "environment" in body
        assert "default_model" in body
        assert "timestamp" in body

        # Nested structures expected by the app
        assert isinstance(body.get("relay"), dict)
        assert isinstance(body.get("openai"), dict)
        assert isinstance(body.get("meta"), dict)


@pytest.mark.integration
async def test_responses_non_streaming_basic(async_client: httpx.AsyncClient) -> None:
    payload = {
        "model": settings.DEFAULT_MODEL,
        "input": "Say hello from the local relay.",
    }

    resp = await async_client.post("/v1/responses", json=payload)
    assert resp.status_code == 200

    body = resp.json()
    assert body.get("object") == "response"
    assert isinstance(body.get("output"), list)
    assert body["output"], "output list should not be empty"

    first_msg = body["output"][0]
    assert first_msg.get("type") == "message"
    assert first_msg.get("role") == "assistant"
    assert isinstance(first_msg.get("content"), list)
    assert first_msg["content"], "content list should not be empty"

    first_part = first_msg["content"][0]
    assert first_part.get("type") == "output_text"
    text = first_part.get("text", "")
    assert isinstance(text, str)
    assert text.strip(), "assistant text should not be empty"
    # Soft semantic check
    assert "hello" in text.lower()


@pytest.mark.integration
async def test_responses_streaming_sse_basic(async_client: httpx.AsyncClient) -> None:
    """
    Verify that the relay streams SSE events in the same shape as api.openai.com.

    We do not fully parse every event; we just assert that:
      - The HTTP status is 200
      - The SSE stream includes at least one `response.output_text.delta`
      - The SSE stream ends with `response.completed`
    """
    payload = {
        "model": settings.DEFAULT_MODEL,
        "input": "Stream a short message.",
        "stream": True,
    }

    async with async_client.stream("POST", "/v1/responses", json=payload) as resp:
        assert resp.status_code == 200

        chunks: list[str] = []
        async for text_chunk in resp.aiter_text():
            chunks.append(text_chunk)

    stream_text = "".join(chunks)
    # Basic SSE framing guarantees lines starting with "event: ..."
    assert "event: response.output_text.delta" in stream_text
    assert "event: response.completed" in stream_text
    # There should also be at least one "data: " line
    assert "data:" in stream_text


@pytest.mark.integration
async def test_embeddings_basic(async_client: httpx.AsyncClient) -> None:
    """
    Simple check that the relay can forward /v1/embeddings and the shape matches
    OpenAI's embeddings API.
    """
    payload = {
        "model": "text-embedding-3-small",
        "input": "Testing embeddings via the local relay.",
    }

    resp = await async_client.post("/v1/embeddings", json=payload)
    assert resp.status_code == 200

    body = resp.json()
    # OpenAI embeddings responses are {"object": "list", "data": [...], ...}
    assert body.get("object") == "list"
    assert isinstance(body.get("data"), list)
    assert body["data"], "embeddings data list should not be empty"

    first_item = body["data"][0]
    assert "embedding" in first_item
    embedding = first_item["embedding"]
    assert isinstance(embedding, list)
    assert embedding, "embedding vector should not be empty"


@pytest.mark.integration
async def test_models_list_basic(async_client: httpx.AsyncClient) -> None:
    """
    Basic sanity check on /v1/models list endpoint.
    """
    resp = await async_client.get("/v1/models")
    assert resp.status_code == 200

    body = resp.json()
    assert body.get("object") == "list"
    assert isinstance(body.get("data"), list)

    # There should be at least one model with an "id"
    assert body["data"], "models list should not be empty"
    assert any(isinstance(m, dict) and "id" in m for m in body["data"])


@pytest.mark.integration
async def test_models_retrieve_default_model(async_client: httpx.AsyncClient) -> None:
    """
    Retrieve settings.DEFAULT_MODEL via /v1/models/{id} and check the shape.
    """
    model_id = settings.DEFAULT_MODEL

    resp = await async_client.get(f"/v1/models/{model_id}")
    assert resp.status_code == 200

    body = resp.json()
    assert body.get("object") == "model"
    assert body.get("id") == model_id
    # Optional extra checks if upstream includes them
    # e.g. "created", "owned_by", etc. – but we do not require them here

@pytest.mark.integration
async def test_responses_compact_basic(async_client: httpx.AsyncClient) -> None:
    payload = {
        "model": settings.DEFAULT_MODEL,
        "input": [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"},
        ],
    }

    resp = await async_client.post("/v1/responses/compact", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["object"] == "response.compaction"


@pytest.mark.integration
async def test_tools_manifest_has_responses_endpoints(async_client: httpx.AsyncClient) -> None:
    resp = await async_client.get("/manifest")
    assert resp.status_code == 200
    data = resp.json()
    assert "/v1/responses" in data["endpoints"]["responses"]
    assert "/v1/responses/compact" in data["endpoints"]["responses_compact"]
```

## FILE: tests/test_relay_auth_guard.py @ 4a039730f9a85ddb91f1a6f031321c2d232c27e1
```
# tests/test_relay_auth_guard.py
from __future__ import annotations

import os

import httpx
import pytest

from app.main import app

# All tests here are async
pytestmark = pytest.mark.asyncio


@pytest.mark.integration
@pytest.mark.skipif(
    os.getenv("RELAY_AUTH_ENABLED", "false").lower() != "true",
    reason="Set RELAY_AUTH_ENABLED=true to run auth guard test",
)
async def test_responses_requires_valid_relay_key() -> None:
    """
    When RELAY_AUTH_ENABLED=true and no relay key is provided, the relay
    must reject the request with 401/403 rather than silently forwarding.
    """
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
        timeout=30.0,
    ) as client:
        # No Authorization, no X-Relay-Key
        resp = await client.post(
            "/v1/responses",
            json={"model": "gpt-5.1", "input": "Should not succeed"},
        )

    assert resp.status_code in (401, 403)
```

## BASELINE (static/)

## FILE: static/.well-known/__init__.py @ 4a039730f9a85ddb91f1a6f031321c2d232c27e1
```
```

## FILE: static/.well-known/ai-plugin.json @ 4a039730f9a85ddb91f1a6f031321c2d232c27e1
```
{
  "schema_version": "v1",
  "name_for_human": "ChatGPT Team Relay",
  "name_for_model": "chatgpt_team_relay",
  "description_for_human": "A relay that forwards ChatGPT-style requests to the OpenAI API with custom routing, logging, and tools.",
  "description_for_model": "You are calling a relay service that forwards requests to the OpenAI API. Prefer the /v1/responses endpoint for chat-style interactions. Use /v1/tools to discover available actions and /v1/realtime/sessions only when you need a realtime session.",
  "auth": {
    "type": "none"
  },
  "api": {
    "type": "openapi",
    "url": "https://chatgpt-team-relay.onrender.com/openapi.yaml",
    "has_user_authentication": false
  },
  "logo_url": "https://chatgpt-team-relay.onrender.com/static/logo.png",
  "contact_email": "support@example.com",
  "legal_info_url": "https://example.com/legal",
  "terms_of_service_url": "https://example.com/terms",
  "privacy_policy_url": "https://example.com/privacy",
  "settings": {
    "use_user_consent_on_first_use": false
  }
}
```

## BASELINE (schemas/)

## FILE: schemas/__init__.py @ 4a039730f9a85ddb91f1a6f031321c2d232c27e1
```
```

## FILE: schemas/openapi.yaml @ 4a039730f9a85ddb91f1a6f031321c2d232c27e1
```
openapi: 3.1.0
info:
  title: ChatGPT Team Relay
  version: "1.0.0"
  description: |
    OpenAPI description for the ChatGPT Team Relay.

    This relay exposes a thin, OpenAI-compatible proxy surface:

      • /v1/responses
      • /v1/embeddings
      • /v1/models
      • /v1/files
      • /v1/vector_stores
      • /v1/images
      • /v1/videos
      • /v1/conversations
      • /v1/realtime/sessions

    It also provides local utility endpoints under /actions and /v1/actions
    plus a tools manifest at /v1/tools for ChatGPT Actions.

servers:
  - url: https://chatgpt-team-relay.onrender.com

paths:
  /health:
    get:
      operationId: getHealth
      summary: Health check
      responses:
        "200":
          description: Relay is healthy
          content:
            application/json:
              schema:
                type: object
                properties:
                  status:
                    type: string
                  mode:
                    type: string
                  environment:
                    type: string

  /v1/health:
    get:
      operationId: getHealthV1
      summary: v1-style health check
      responses:
        "200":
          description: Relay is healthy
          content:
            application/json:
              schema:
                type: object
                properties:
                  status:
                    type: string
                  mode:
                    type: string
                  environment:
                    type: string

  /v1/responses:
    post:
      operationId: createResponse
      summary: Create a response
      description: |
        Thin proxy to the OpenAI Responses API.
        Supports both non-stream and stream=true modes.
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              description: OpenAI Responses request payload.
      responses:
        "200":
          description: Response object from the OpenAI Responses API
          content:
            application/json:
              schema:
                type: object

  /v1/responses/{response_id}:
    get:
      operationId: retrieveResponse
      summary: Retrieve a response by ID
      parameters:
        - name: response_id
          in: path
          required: true
          schema:
            type: string
      responses:
        "200":
          description: Response object
          content:
            application/json:
              schema:
                type: object

  /v1/responses/{response_id}/cancel:
    post:
      operationId: cancelResponse
      summary: Cancel a running response
      parameters:
        - name: response_id
          in: path
          required: true
          schema:
            type: string
      responses:
        "200":
          description: Cancellation acknowledgement
          content:
            application/json:
              schema:
                type: object

  /v1/embeddings:
    post:
      operationId: createEmbedding
      summary: Create embeddings
      description: Thin proxy to the OpenAI Embeddings API.
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
      responses:
        "200":
          description: Embedding result
          content:
            application/json:
              schema:
                type: object

  /v1/models:
    get:
      operationId: listModels
      summary: List models
      responses:
        "200":
          description: List of models
          content:
            application/json:
              schema:
                type: object

  /v1/models/{model_id}:
    get:
      operationId: retrieveModel
      summary: Retrieve a model
      parameters:
        - name: model_id
          in: path
          required: true
          schema:
            type: string
      responses:
        "200":
          description: Model details
          content:
            application/json:
              schema:
                type: object

  /v1/files:
    get:
      operationId: listFiles
      summary: List files
      responses:
        "200":
          description: List of files
          content:
            application/json:
              schema:
                type: object
    post:
      operationId: createFile
      summary: Upload a file
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
      responses:
        "200":
          description: File metadata
          content:
            application/json:
              schema:
                type: object

  /v1/files/{file_id}:
    get:
      operationId: retrieveFile
      summary: Retrieve file metadata
      parameters:
        - name: file_id
          in: path
          required: true
          schema:
            type: string
      responses:
        "200":
          description: File metadata
          content:
            application/json:
              schema:
                type: object
    delete:
      operationId: deleteFile
      summary: Delete a file
      parameters:
        - name: file_id
          in: path
          required: true
          schema:
            type: string
      responses:
        "200":
          description: File deletion confirmation
          content:
            application/json:
              schema:
                type: object

  /v1/vector_stores:
    get:
      operationId: listVectorStores
      summary: List vector stores
      responses:
        "200":
          description: List of vector stores
          content:
            application/json:
              schema:
                type: object
    post:
      operationId: createVectorStore
      summary: Create a vector store
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
      responses:
        "200":
          description: Vector store object
          content:
            application/json:
              schema:
                type: object

  /v1/vector_stores/{vector_store_id}:
    get:
      operationId: retrieveVectorStore
      summary: Retrieve a vector store
      parameters:
        - name: vector_store_id
          in: path
          required: true
          schema:
            type: string
      responses:
        "200":
          description: Vector store object
          content:
            application/json:
              schema:
                type: object

  /v1/images:
    post:
      operationId: createImagesRoot
      summary: Best-effort image generation entrypoint
      description: Thin proxy to the OpenAI Images API for legacy clients.
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
      responses:
        "200":
          description: Image generation response
          content:
            application/json:
              schema:
                type: object

  /v1/images/generations:
    post:
      operationId: createImageGenerations
      summary: Generate images from a prompt
      description: Thin proxy to the OpenAI Images /images/generations endpoint.
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
      responses:
        "200":
          description: Image generation response
          content:
            application/json:
              schema:
                type: object

  /v1/videos:
    post:
      operationId: createVideoJob
      summary: Create a video generation job
      description: Thin proxy to the OpenAI Videos API (job creation).
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
      responses:
        "200":
          description: Video job object
          content:
            application/json:
              schema:
                type: object

  /v1/videos/{video_path}:
    get:
      operationId: getVideoJobOrContent
      summary: Retrieve a video job or content
      parameters:
        - name: video_path
          in: path
          required: true
          schema:
            type: string
          description: |
            Path under /v1/videos, e.g. "jobs/{id}", "jobs/{id}/content".
      responses:
        "200":
          description: Video job or content
          content:
            application/json:
              schema:
                type: object

  /v1/conversations:
    get:
      operationId: listConversations
      summary: List conversations
      responses:
        "200":
          description: List of conversations
          content:
            application/json:
              schema:
                type: object
    post:
      operationId: createConversation
      summary: Create a conversation
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
      responses:
        "200":
          description: Conversation object
          content:
            application/json:
              schema:
                type: object

  /v1/conversations/{conversation_id}:
    get:
      operationId: retrieveConversation
      summary: Retrieve a conversation
      parameters:
        - name: conversation_id
          in: path
          required: true
          schema:
            type: string
      responses:
        "200":
          description: Conversation object
          content:
            application/json:
              schema:
                type: object
    delete:
      operationId: deleteConversation
      summary: Delete a conversation
      parameters:
        - name: conversation_id
          in: path
          required: true
          schema:
            type: string
      responses:
        "200":
          description: Deletion confirmation
          content:
            application/json:
              schema:
                type: object

  /v1/conversations/{conversation_id}/messages:
    get:
      operationId: listConversationMessages
      summary: List messages in a conversation
      parameters:
        - name: conversation_id
          in: path
          required: true
          schema:
            type: string
      responses:
        "200":
          description: List of messages
          content:
            application/json:
              schema:
                type: object
    post:
      operationId: createConversationMessage
      summary: Add a message to a conversation
      parameters:
        - name: conversation_id
          in: path
          required: true
          schema:
            type: string
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
      responses:
        "200":
          description: Message object
          content:
            application/json:
              schema:
                type: object

  /v1/realtime/sessions:
    post:
      operationId: createRealtimeSession
      summary: Create a Realtime session
      description: Thin proxy to the OpenAI Realtime Sessions API.
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
      responses:
        "200":
          description: Realtime session object
          content:
            application/json:
              schema:
                type: object

  /v1/tools:
    get:
      operationId: listTools
      summary: List tools from the tools manifest
      responses:
        "200":
          description: List of tools
          content:
            application/json:
              schema:
                type: object

  /v1/tools/{tool_id}:
    get:
      operationId: retrieveTool
      summary: Retrieve a single tool definition
      parameters:
        - name: tool_id
          in: path
          required: true
          schema:
            type: string
      responses:
        "200":
          description: Tool definition
          content:
            application/json:
              schema:
                type: object

  /actions/ping:
    get:
      operationId: actionsPing
      summary: Simple ping at /actions
      responses:
        "200":
          description: Ping OK
          content:
            application/json:
              schema:
                type: object

  /v1/actions/ping:
    get:
      operationId: v1ActionsPing
      summary: Simple ping at /v1/actions
      responses:
        "200":
          description: Ping OK
          content:
            application/json:
              schema:
                type: object

  /actions/relay_info:
    get:
      operationId: actionsRelayInfo
      summary: Relay information (actions)
      responses:
        "200":
          description: Relay info object
          content:
            application/json:
              schema:
                type: object

  /v1/actions/relay_info:
    get:
      operationId: v1ActionsRelayInfo
      summary: Relay information (v1/actions)
      responses:
        "200":
          description: Relay info object
          content:
            application/json:
              schema:
                type: object

components: {}
```

