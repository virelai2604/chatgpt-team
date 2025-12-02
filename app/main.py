# app/main.py
"""
main.py — ChatGPT Team Relay Entry Point
────────────────────────────────────────
Unified app bootstrap for the OpenAI-compatible relay.

Features:
  • Forwards all /v1/* calls to the upstream OpenAI API, except
    for a small set of local endpoints.
  • Integrates JSON validation + orchestration middleware.
  • Registers /v1/tools from the hosted tools manifest.
  • Serves /schemas/openapi.yaml for ChatGPT Actions / Plugins.
  • Exposes /health and /v1/health for health checks.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from app.core.config import settings
from app.middleware.p4_orchestrator import P4OrchestratorMiddleware
from app.middleware.relay_auth import RelayAuthMiddleware
from app.middleware.validation import SchemaValidationMiddleware
from app.routes.register_routes import register_routes


def create_app() -> FastAPI:
    # Load .env (no-op on Render where env vars are already injected)
    load_dotenv()

    relay_name = os.getenv("RELAY_NAME", settings.RELAY_NAME)
    bifl_version = os.getenv("BIFL_VERSION", "dev")
    environment = settings.ENVIRONMENT

    # Core configuration from settings
    openai_api_base = str(settings.OPENAI_API_BASE)
    default_model = settings.DEFAULT_MODEL
    validation_schema_path = settings.VALIDATION_SCHEMA_PATH
    tools_manifest_path = settings.TOOLS_MANIFEST

    app = FastAPI(
        title=relay_name,
        version=bifl_version,
        docs_url=None,
        redoc_url=None,
    )

    # Store config on app.state for use by other modules if needed
    app.state.OPENAI_API_BASE = openai_api_base
    app.state.DEFAULT_MODEL = default_model
    app.state.ENVIRONMENT = environment
    app.state.VALIDATION_SCHEMA_PATH = validation_schema_path
    app.state.TOOLS_MANIFEST = tools_manifest_path

    # ------------------------------------------------------------
    # CORS
    # ------------------------------------------------------------
    origins_raw = settings.CORS_ALLOW_ORIGINS
    allow_origins = [o.strip() for o in origins_raw.split(",") if o.strip()]

    methods_raw = settings.CORS_ALLOW_METHODS
    allow_methods = [m.strip() for m in methods_raw.split(",") if m.strip()]

    headers_raw = settings.CORS_ALLOW_HEADERS
    allow_headers = [h.strip() for h in headers_raw.split(",") if h.strip()]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins or ["*"],
        allow_methods=allow_methods or ["*"],
        allow_headers=allow_headers or ["*"],
    )

    # ------------------------------------------------------------
    # Middleware stack: validation → auth → orchestrator → routes
    # ------------------------------------------------------------
    app.add_middleware(SchemaValidationMiddleware)
    if settings.RELAY_AUTH_ENABLED:
        app.add_middleware(RelayAuthMiddleware, relay_key=settings.RELAY_KEY)
    app.add_middleware(P4OrchestratorMiddleware)

    # ------------------------------------------------------------
    # Meta endpoints
    # ------------------------------------------------------------
    @app.get("/")
    async def root() -> dict:
        return {
            "object": "relay",
            "name": relay_name,
            "version": bifl_version,
            "environment": environment,
            "default_model": default_model,
            "openai_api_base": openai_api_base,
        }

    # Keep /health and /v1/health implemented at routes.health,
    # but provide a minimal fallback here if needed.
    @app.get("/health-basic")
    async def health_basic() -> JSONResponse:
        return JSONResponse(
            {
                "status": "ok",
                "environment": environment,
                "default_model": default_model,
            }
        )

    # OpenAPI schema for ChatGPT Actions / Plugins
    @app.get("/schemas/openapi.yaml")
    async def openapi_schema() -> FileResponse:
        schema_path_env = os.getenv("OPENAPI_SCHEMA_PATH", "schemas/openapi.yaml")
        schema_path = Path(schema_path_env)
        if not schema_path.is_file():
            # 404 if schema missing
            return FileResponse(
                path=schema_path,
                status_code=404,
            )
        return FileResponse(path=schema_path, media_type="text/yaml")

    # Common alias used by some tooling
    @app.get("/openapi.yaml")
    async def openapi_schema_root() -> FileResponse:
        return await openapi_schema()  # type: ignore[func-returns-value]

    # ------------------------------------------------------------
    # Register routes
    # ------------------------------------------------------------
    register_routes(app)

    return app


app = create_app()
