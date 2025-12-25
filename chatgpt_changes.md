# ChatGPT Sync
Repo: chatgpt-team
Base: origin/main
Base commit (merge-base): 834ed1053166c0c0551d2195ee113f003ee84712
Dirs: app tests static schemas src scripts/src
Root files: project-tree.md pyproject.toml chatgpt_sync.sh AGENTS.md __init__.py generate_tree.py
Mode: changes
Generated: 2025-12-25T11:07:59+07:00

## CHANGE SUMMARY (since 834ed1053166c0c0551d2195ee113f003ee84712, includes worktree)

```
M	app/main.py
M	app/middleware/relay_auth.py
M	app/routes/health.py
M	tests/conftest.py
```

## PATCH (since 834ed1053166c0c0551d2195ee113f003ee84712, includes worktree)

```diff
diff --git a/app/main.py b/app/main.py
index 12b2137..1e5e682 100755
--- a/app/main.py
+++ b/app/main.py
@@ -1,73 +1,50 @@
-import os
+from __future__ import annotations
 
 from fastapi import FastAPI
 from fastapi.middleware.cors import CORSMiddleware
 
-from app.api.sse import create_sse_app
+from app.api.sse import router as sse_router
+from app.api.tools_api import router as tools_router
 from app.core.config import get_settings
-from app.middleware.p4_orchestrator import P4OrchestratorMiddleware
 from app.middleware.relay_auth import RelayAuthMiddleware
 from app.routes.register_routes import register_routes
-from app.utils.logger import configure_logging
-
-
-def _get_bool_setting(settings, snake: str, upper: str, default: bool) -> bool:
-    if hasattr(settings, snake):
-        v = getattr(settings, snake)
-        if isinstance(v, bool):
-            return v
-        if isinstance(v, str):
-            return v.strip().lower() in {"1", "true", "yes", "on"}
-
-    if hasattr(settings, upper):
-        v = getattr(settings, upper)
-        if isinstance(v, bool):
-            return v
-        if isinstance(v, str):
-            return v.strip().lower() in {"1", "true", "yes", "on"}
-
-    return default
+from app.utils.logger import relay_log as logger
 
 
 def create_app() -> FastAPI:
     settings = get_settings()
-    configure_logging(settings)
-
-    enable_stream = _get_bool_setting(settings, "enable_stream", "ENABLE_STREAM", True)
 
     app = FastAPI(
-        title="ChatGPT Team Relay",
-        version=os.getenv("RELAY_VERSION", "0.0.0"),
-        docs_url=None,
-        redoc_url=None,
-        openapi_url="/openapi.json",
+        title="chatgpt-team-relay",
+        version="0.1.0",
     )
 
-    # Orchestrator (logging / request context)
-    app.add_middleware(P4OrchestratorMiddleware)
-
     # CORS
     app.add_middleware(
         CORSMiddleware,
-        allow_origins=settings.CORS_ORIGINS or ["*"],
-        allow_credentials=True,
-        allow_methods=["*"],
-        allow_headers=["*"],
+        allow_origins=settings.CORS_ALLOW_ORIGINS,
+        allow_methods=settings.CORS_ALLOW_METHODS,
+        allow_headers=settings.CORS_ALLOW_HEADERS,
+        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
     )
 
-    # IMPORTANT:
-    # Always install RelayAuthMiddleware so tests can toggle RELAY_AUTH_ENABLED via monkeypatch
-    # even if the app was created while RELAY_AUTH_ENABLED=false.
-    #
-    # The middleware itself is a no-op when RELAY_AUTH_ENABLED is false.
+    # Always install relay auth middleware.
+    # Whether it enforces auth is controlled at request-time (settings flags),
+    # which is required for tests that monkeypatch settings without rebuilding the app.
     app.add_middleware(RelayAuthMiddleware)
+    if getattr(settings, "RELAY_AUTH_ENABLED", False) and getattr(settings, "RELAY_KEY", ""):
+        logger.info("Relay auth enabled (RELAY_AUTH_ENABLED=true).")
+    else:
+        logger.info("Relay auth disabled (RELAY_AUTH_ENABLED=false or RELAY_KEY missing).")
 
-    # Routes
+    # Register all route modules
     register_routes(app)
 
-    # SSE mounting (non-actions clients)
-    if enable_stream:
-        app.mount("/v1/responses:stream", create_sse_app())
+    # Tool manifest / helper endpoints
+    app.include_router(tools_router)
+
+    # SSE streaming endpoints (non-Actions surface)
+    app.include_router(sse_router)
 
     return app
 
diff --git a/app/middleware/relay_auth.py b/app/middleware/relay_auth.py
index 5ba1e79..5e9575c 100755
--- a/app/middleware/relay_auth.py
+++ b/app/middleware/relay_auth.py
@@ -1,90 +1,101 @@
-# app/middleware/relay_auth.py
-
 from __future__ import annotations
 
-from typing import Awaitable, Callable
+from typing import Optional
 
-from fastapi import HTTPException, Request
-from fastapi.responses import JSONResponse, Response
 from starlette.middleware.base import BaseHTTPMiddleware
+from starlette.requests import Request
+from starlette.responses import JSONResponse, Response
 
-from app.utils.authy import check_relay_key
-from app.utils.logger import get_logger
-
-logger = get_logger(__name__)
-
-# Exact paths that should always be public
-SAFE_EXACT_PATHS = {
-    "/",  # root
-    "/health",
-    "/health/",
-    "/v1/health",
-    "/v1/health/",
-    "/actions/ping",
-    "/actions/relay_info",
-    "/v1/actions/ping",
-    "/v1/actions/relay_info",
-}
-
-# Prefixes that should always be public (docs, openapi, assets, etc.)
-SAFE_PREFIXES = (
-    "/docs",
-    "/redoc",
-    "/openapi.json",
-    "/static",
-    "/favicon",
-)
+from app.core.config import settings
+from app.utils.logger import relay_log as logger
 
 
-class RelayAuthMiddleware(BaseHTTPMiddleware):
+def _is_public_path(path: str) -> bool:
+    # Always-public health & docs/bootstrap endpoints
+    if path in {"/", "/health", "/v1/health"}:
+        return True
+    if path in {"/openapi.json", "/docs", "/redoc", "/manifest"}:
+        return True
+    # Actions helper endpoints are usually safe to keep public.
+    if path.startswith("/v1/actions/"):
+        return True
+    return False
+
+
+def _valid_tokens() -> set[str]:
     """
-    Optional shared-secret auth in front of the relay.
+    Tokens that should be accepted for relay authentication.
+
+    Primary token: settings.RELAY_KEY
+    Optional token: settings.RELAY_AUTH_TOKEN (if present)
+    """
+    tokens: set[str] = set()
+    relay_key = getattr(settings, "RELAY_KEY", "") or ""
+    auth_token = getattr(settings, "RELAY_AUTH_TOKEN", "") or ""
+    if relay_key:
+        tokens.add(relay_key)
+    if auth_token:
+        tokens.add(auth_token)
+    return tokens
+
+
+def _extract_bearer_token(authorization: str) -> Optional[str]:
+    parts = authorization.split(None, 1)
+    if len(parts) != 2:
+        return None
+    scheme, token = parts[0], parts[1]
+    if scheme.lower() != "bearer":
+        return None
+    token = token.strip()
+    return token or None
 
-    Controlled by env / settings:
 
-      - RELAY_KEY (or legacy RELAY_AUTH_TOKEN)
-      - RELAY_AUTH_ENABLED (bool)
+class RelayAuthMiddleware(BaseHTTPMiddleware):
+    """
+    Gateway-style auth guard.
 
-    Behavior:
+    Key behavior:
+    - Middleware is installed unconditionally in app/main.py.
+    - Enforcement is conditional at request-time:
+        settings.RELAY_AUTH_ENABLED and (RELAY_KEY or RELAY_AUTH_TOKEN)
 
-      - Health + docs + actions ping/info are always public.
-      - Non-/v1/ paths remain public.
-      - /v1/* paths are protected when RELAY_AUTH_ENABLED is True.
+    This supports tests that monkeypatch settings without rebuilding the ASGI app.
     """
 
-    async def dispatch(
-        self,
-        request: Request,
-        call_next: Callable[[Request], Awaitable[Response]],
-    ) -> Response:
+    async def dispatch(self, request: Request, call_next) -> Response:
         path = request.url.path
 
-        # Public routes
-        if path in SAFE_EXACT_PATHS or path.startswith(SAFE_PREFIXES):
+        if _is_public_path(path):
             return await call_next(request)
 
-        # Only protect OpenAI-style API paths under /v1
+        # Only enforce when explicitly enabled.
+        if not bool(getattr(settings, "RELAY_AUTH_ENABLED", False)):
+            return await call_next(request)
+
+        allowed_tokens = _valid_tokens()
+        if not allowed_tokens:
+            logger.warning("Relay auth enabled but no RELAY_KEY/RELAY_AUTH_TOKEN set; allowing request.")
+            return await call_next(request)
+
+        # Scope: protect /v1/* by default
         if not path.startswith("/v1/"):
             return await call_next(request)
 
-        auth_header = request.headers.get("Authorization")
-        x_relay_key = request.headers.get("X-Relay-Key")
-
-        try:
-            # Will no-op if RELAY_AUTH_ENABLED is False
-            check_relay_key(auth_header=auth_header, x_relay_key=x_relay_key)
-        except HTTPException as exc:
-            # DO NOT let this bubble out as an exception to httpx;
-            # convert to a normal JSON error response.
-            logger.warning(
-                "Relay auth failed",
-                extra={"path": path, "method": request.method, "detail": exc.detail},
-            )
-            return JSONResponse(
-                status_code=exc.status_code,
-                content={"detail": exc.detail},
-                headers=getattr(exc, "headers", None) or {},
-            )
-
-        # Auth OK (or disabled)
-        return await call_next(request)
+        # Accept either X-Relay-Key or Authorization: Bearer <token>
+        x_relay_key = request.headers.get("x-relay-key")
+        if x_relay_key and x_relay_key in allowed_tokens:
+            return await call_next(request)
+
+        authorization = request.headers.get("authorization")
+        if authorization:
+            token = _extract_bearer_token(authorization)
+            if token is None:
+                return JSONResponse(
+                    status_code=401,
+                    content={"detail": "Authorization header must be 'Bearer <token>'."},
+                )
+            if token not in allowed_tokens:
+                return JSONResponse(status_code=401, content={"detail": "Invalid relay key."})
+            return await call_next(request)
+
+        return JSONResponse(status_code=401, content={"detail": "Missing relay key."})
diff --git a/app/routes/health.py b/app/routes/health.py
index 32136c7..3baa6b9 100755
--- a/app/routes/health.py
+++ b/app/routes/health.py
@@ -1,6 +1,6 @@
 from __future__ import annotations
 
-import time
+import sys
 from datetime import datetime, timezone
 from typing import Any, Dict
 
@@ -8,45 +8,52 @@ from fastapi import APIRouter
 
 from app.core.config import settings
 
-router = APIRouter(tags=["health"])
-
-_START_TIME = time.time()
+router = APIRouter()
 
 
 def _health_payload() -> Dict[str, Any]:
-    now = datetime.now(timezone.utc)
+    """
+    Health contract expected by the current tests:
+      - object/status
+      - environment/default_model/timestamp
+      - relay/openai/meta dicts
+    """
+    ts = datetime.now(timezone.utc).isoformat()
+
+    environment = getattr(settings, "ENVIRONMENT", "unknown")
+    app_mode = getattr(settings, "APP_MODE", "unknown")
+    default_model = getattr(settings, "DEFAULT_MODEL", None)
 
     return {
         "object": "health",
         "status": "ok",
-        "environment": settings.ENVIRONMENT,
-        "default_model": settings.DEFAULT_MODEL,
-        "timestamp": now.isoformat(),
-        # Nested structures expected by tests
+        "environment": environment,
+        "default_model": default_model,
+        "timestamp": ts,
         "relay": {
-            "name": settings.RELAY_NAME,
-            "app_mode": settings.APP_MODE,
+            "app_mode": app_mode,
             "auth_enabled": bool(getattr(settings, "RELAY_AUTH_ENABLED", False)),
         },
         "openai": {
-            "base_url": settings.OPENAI_BASE_URL,
+            "base_url": getattr(settings, "OPENAI_BASE_URL", None),
+            "has_api_key": bool(getattr(settings, "OPENAI_API_KEY", "")),
         },
         "meta": {
-            "uptime_seconds": round(time.time() - _START_TIME, 3),
+            "python": sys.version.split()[0],
         },
     }
 
 
-@router.get("/", summary="Health check")
-async def root_ping() -> Dict[str, Any]:
+@router.get("/")
+async def root() -> Dict[str, Any]:
     return _health_payload()
 
 
-@router.get("/health", summary="Health check")
+@router.get("/health")
 async def health() -> Dict[str, Any]:
     return _health_payload()
 
 
-@router.get("/v1/health", summary="Health check")
+@router.get("/v1/health")
 async def v1_health() -> Dict[str, Any]:
     return _health_payload()
diff --git a/tests/conftest.py b/tests/conftest.py
index e729b18..2573524 100755
--- a/tests/conftest.py
+++ b/tests/conftest.py
@@ -1,45 +1,26 @@
-import os
+from __future__ import annotations
 
 import httpx
-import pytest
+import pytest_asyncio
 
+from app.main import app as fastapi_app
 
-@pytest.fixture(scope="session")
-def relay_base_url() -> str:
-    return os.getenv("RELAY_BASE_URL", "http://localhost:8000")
 
-
-@pytest.fixture(scope="session")
-def relay_token() -> str:
-    return os.getenv("RELAY_TOKEN", "")
-
-
-@pytest.fixture(scope="session")
-async def client(relay_base_url: str, relay_token: str):
+@pytest_asyncio.fixture
+async def async_client() -> httpx.AsyncClient:
     """
-    Default integration client.
+    Async HTTP client bound to the in-process FastAPI app.
 
-    Important: The test suite sets relay auth OFF by default so local tests run
-    without requiring a key. Individual tests can monkeypatch settings to enable it.
+    tests/test_local_e2e.py expects an `async_client` fixture.
     """
-    os.environ.setdefault("RELAY_AUTH_ENABLED", "false")
-    os.environ.setdefault("RELAY_KEY", "dummy")
-
-    headers: dict[str, str] = {}
-    if relay_token:
-        headers["Authorization"] = f"Bearer {relay_token}"
-
-    async with httpx.AsyncClient(
-        base_url=relay_base_url,
-        headers=headers,
-        timeout=60.0,
-    ) as ac:
-        yield ac
+    transport = httpx.ASGITransport(app=fastapi_app)
+    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
+        yield c
 
 
-@pytest.fixture(scope="session")
-async def async_client(client: httpx.AsyncClient) -> httpx.AsyncClient:
+@pytest_asyncio.fixture
+async def client(async_client: httpx.AsyncClient) -> httpx.AsyncClient:
     """
-    Alias fixture for tests that expect `async_client` by name.
+    Backwards-compatible alias. Some tests use `client`.
     """
-    return client
+    yield async_client
```

## CURRENT CONTENT OF CHANGED FILES (WORKTREE)

## FILE: app/main.py @ WORKTREE
```
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.sse import router as sse_router
from app.api.tools_api import router as tools_router
from app.core.config import get_settings
from app.middleware.relay_auth import RelayAuthMiddleware
from app.routes.register_routes import register_routes
from app.utils.logger import relay_log as logger


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="chatgpt-team-relay",
        version="0.1.0",
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ALLOW_ORIGINS,
        allow_methods=settings.CORS_ALLOW_METHODS,
        allow_headers=settings.CORS_ALLOW_HEADERS,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    )

    # Always install relay auth middleware.
    # Whether it enforces auth is controlled at request-time (settings flags),
    # which is required for tests that monkeypatch settings without rebuilding the app.
    app.add_middleware(RelayAuthMiddleware)
    if getattr(settings, "RELAY_AUTH_ENABLED", False) and getattr(settings, "RELAY_KEY", ""):
        logger.info("Relay auth enabled (RELAY_AUTH_ENABLED=true).")
    else:
        logger.info("Relay auth disabled (RELAY_AUTH_ENABLED=false or RELAY_KEY missing).")

    # Register all route modules
    register_routes(app)

    # Tool manifest / helper endpoints
    app.include_router(tools_router)

    # SSE streaming endpoints (non-Actions surface)
    app.include_router(sse_router)

    return app


app = create_app()
```

## FILE: app/middleware/relay_auth.py @ WORKTREE
```
from __future__ import annotations

from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import settings
from app.utils.logger import relay_log as logger


def _is_public_path(path: str) -> bool:
    # Always-public health & docs/bootstrap endpoints
    if path in {"/", "/health", "/v1/health"}:
        return True
    if path in {"/openapi.json", "/docs", "/redoc", "/manifest"}:
        return True
    # Actions helper endpoints are usually safe to keep public.
    if path.startswith("/v1/actions/"):
        return True
    return False


def _valid_tokens() -> set[str]:
    """
    Tokens that should be accepted for relay authentication.

    Primary token: settings.RELAY_KEY
    Optional token: settings.RELAY_AUTH_TOKEN (if present)
    """
    tokens: set[str] = set()
    relay_key = getattr(settings, "RELAY_KEY", "") or ""
    auth_token = getattr(settings, "RELAY_AUTH_TOKEN", "") or ""
    if relay_key:
        tokens.add(relay_key)
    if auth_token:
        tokens.add(auth_token)
    return tokens


def _extract_bearer_token(authorization: str) -> Optional[str]:
    parts = authorization.split(None, 1)
    if len(parts) != 2:
        return None
    scheme, token = parts[0], parts[1]
    if scheme.lower() != "bearer":
        return None
    token = token.strip()
    return token or None


class RelayAuthMiddleware(BaseHTTPMiddleware):
    """
    Gateway-style auth guard.

    Key behavior:
    - Middleware is installed unconditionally in app/main.py.
    - Enforcement is conditional at request-time:
        settings.RELAY_AUTH_ENABLED and (RELAY_KEY or RELAY_AUTH_TOKEN)

    This supports tests that monkeypatch settings without rebuilding the ASGI app.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path

        if _is_public_path(path):
            return await call_next(request)

        # Only enforce when explicitly enabled.
        if not bool(getattr(settings, "RELAY_AUTH_ENABLED", False)):
            return await call_next(request)

        allowed_tokens = _valid_tokens()
        if not allowed_tokens:
            logger.warning("Relay auth enabled but no RELAY_KEY/RELAY_AUTH_TOKEN set; allowing request.")
            return await call_next(request)

        # Scope: protect /v1/* by default
        if not path.startswith("/v1/"):
            return await call_next(request)

        # Accept either X-Relay-Key or Authorization: Bearer <token>
        x_relay_key = request.headers.get("x-relay-key")
        if x_relay_key and x_relay_key in allowed_tokens:
            return await call_next(request)

        authorization = request.headers.get("authorization")
        if authorization:
            token = _extract_bearer_token(authorization)
            if token is None:
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Authorization header must be 'Bearer <token>'."},
                )
            if token not in allowed_tokens:
                return JSONResponse(status_code=401, content={"detail": "Invalid relay key."})
            return await call_next(request)

        return JSONResponse(status_code=401, content={"detail": "Missing relay key."})
```

## FILE: app/routes/health.py @ WORKTREE
```
from __future__ import annotations

import sys
from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter

from app.core.config import settings

router = APIRouter()


def _health_payload() -> Dict[str, Any]:
    """
    Health contract expected by the current tests:
      - object/status
      - environment/default_model/timestamp
      - relay/openai/meta dicts
    """
    ts = datetime.now(timezone.utc).isoformat()

    environment = getattr(settings, "ENVIRONMENT", "unknown")
    app_mode = getattr(settings, "APP_MODE", "unknown")
    default_model = getattr(settings, "DEFAULT_MODEL", None)

    return {
        "object": "health",
        "status": "ok",
        "environment": environment,
        "default_model": default_model,
        "timestamp": ts,
        "relay": {
            "app_mode": app_mode,
            "auth_enabled": bool(getattr(settings, "RELAY_AUTH_ENABLED", False)),
        },
        "openai": {
            "base_url": getattr(settings, "OPENAI_BASE_URL", None),
            "has_api_key": bool(getattr(settings, "OPENAI_API_KEY", "")),
        },
        "meta": {
            "python": sys.version.split()[0],
        },
    }


@router.get("/")
async def root() -> Dict[str, Any]:
    return _health_payload()


@router.get("/health")
async def health() -> Dict[str, Any]:
    return _health_payload()


@router.get("/v1/health")
async def v1_health() -> Dict[str, Any]:
    return _health_payload()
```

## FILE: tests/conftest.py @ WORKTREE
```
from __future__ import annotations

import httpx
import pytest_asyncio

from app.main import app as fastapi_app


@pytest_asyncio.fixture
async def async_client() -> httpx.AsyncClient:
    """
    Async HTTP client bound to the in-process FastAPI app.

    tests/test_local_e2e.py expects an `async_client` fixture.
    """
    transport = httpx.ASGITransport(app=fastapi_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture
async def client(async_client: httpx.AsyncClient) -> httpx.AsyncClient:
    """
    Backwards-compatible alias. Some tests use `client`.
    """
    yield async_client
```

