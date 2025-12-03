"""
main.py — ChatGPT Team Relay Entry Point
────────────────────────────────────────
Unified app bootstrap for the OpenAI-compatible relay.

Features:
  • Forwards all /v1/* calls to the upstream OpenAI API, except
    for a small set of local endpoints.
  • Integrates JSON validation + orchestration middleware.
  • Registers /v1/tools from the hosted tools manifest.
  • Serves /openapi.yaml for ChatGPT Actions / Plugins.
  • Exposes / and /v1/health for Render health checks.
"""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from app.core.config import settings
from app.middleware.validation import SchemaValidationMiddleware
from app.middleware.p4_orchestrator import P4OrchestratorMiddleware
from app.middleware.relay_auth import RelayAuthMiddleware
from app.routes.register_routes import register_routes
from app.utils.error_handler import install_error_handlers

# Load .env early so pydantic settings can see it (if not already loaded).
load_dotenv()

app = FastAPI(
    title=settings.RELAY_NAME,
    version="0.1.0",
    docs_url=None,
    redoc_url=None,
)


# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Middleware: schema validation + P4 orchestration + relay auth
# ---------------------------------------------------------------------------

# JSON logging / future schema validation hook
app.add_middleware(SchemaValidationMiddleware, schema_path=None)

# Attach AsyncOpenAI client + P4 config to request.state
app.add_middleware(P4OrchestratorMiddleware)

# Optionally enforce relay key for /v1/* and /relay/*
if settings.RELAY_AUTH_ENABLED:
    app.add_middleware(RelayAuthMiddleware, relay_key=settings.RELAY_KEY)


# ---------------------------------------------------------------------------
# Error handling + routes
# ---------------------------------------------------------------------------

install_error_handlers(app)
register_routes(app)


# ---------------------------------------------------------------------------
# OpenAPI yaml for ChatGPT Actions / Plugins
# ---------------------------------------------------------------------------

OPENAPI_YAML_PATH = Path("static/.well-known/openapi.yaml").resolve()


@app.get("/openapi.yaml", include_in_schema=False)
async def openapi_yaml():
    """
    Serve the OpenAPI schema used by ChatGPT Actions / Plugins.

    Returns 404 if the file is not present on disk.
    """
    if OPENAPI_YAML_PATH.is_file():
        return FileResponse(str(OPENAPI_YAML_PATH))

    return JSONResponse(
        status_code=404,
        content={
            "error": {
                "message": "openapi.yaml not found",
                "type": "invalid_request_error",
            }
        },
    )


# ---------------------------------------------------------------------------
# Root health / info
# ---------------------------------------------------------------------------


@app.get("/", include_in_schema=False)
async def root():
    """
    Simple root endpoint for quick diagnostics.
    """
    return JSONResponse(
        {
            "status": "ok",
            "relay": settings.RELAY_NAME,
            "environment": settings.ENVIRONMENT,
            "default_model": settings.DEFAULT_MODEL,
            "realtime_model": settings.REALTIME_MODEL,
        }
    )
