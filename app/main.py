"""
main.py — ChatGPT Team Relay Entry Point
────────────────────────────────────────
Unified app bootstrap for the OpenAI-compatible relay.

Focus:
  • Relay-focus surfaces handled locally:
      - Responses, Conversations, Files, Vector Stores, Embeddings,
        Realtime, Models, Images, Videos, Actions.
  • /v1/tools is a local tools registry for introspection.
  • Everything else under /v1/* is orchestrated and generally forwarded
    to OpenAI via P4OrchestratorMiddleware → forward_openai_request.

This file is “BIFL”: minimal moving parts, stable paths, and
behavior aligned with the official OpenAI API reference.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse

from app.middleware.validation import SchemaValidationMiddleware
from app.middleware.p4_orchestrator import P4OrchestratorMiddleware
from app.utils.error_handler import register_error_handlers
from app.utils.logger import setup_logging

from app.api.tools_api import router as tools_router
from app.routes import (
    actions as actions_routes,
    conversations as conversations_routes,
    embeddings as embeddings_routes,
    files as files_routes,
    images as images_routes,
    models as models_routes,
    realtime as realtime_routes,
    responses as responses_routes,
    vector_stores as vector_stores_routes,
    videos as videos_routes,
)


def create_app() -> FastAPI:
    # Load .env (no-op on Render where env vars are already injected)
    load_dotenv()

    # Initialize logging as early as possible
    setup_logging()

    relay_name = os.getenv("RELAY_NAME", "ChatGPT Team Relay")
    bifl_version = os.getenv("BIFL_VERSION", "dev")
    environment = os.getenv("ENVIRONMENT", "development")

    # Core configuration
    openai_api_base = os.getenv("OPENAI_API_BASE", "https://api.openai.com")
    openai_api_key = os.getenv("OPENAI_API_KEY", "")
    openai_org_id = os.getenv("OPENAI_ORG_ID", "")
    default_model = os.getenv("DEFAULT_MODEL", "gpt-4o-mini")
    validation_schema_path = os.getenv("VALIDATION_SCHEMA_PATH", "")
    tools_manifest_path = os.getenv(
        "TOOLS_MANIFEST",
        "app/manifests/tools_manifest.json",
    )

    app = FastAPI(
        title=relay_name,
        version=bifl_version,
        docs_url=None,
        redoc_url=None,
    )

    # Store config on app.state for use by other modules if needed
    app.state.OPENAI_API_BASE = openai_api_base
    app.state.OPENAI_API_KEY = openai_api_key
    app.state.OPENAI_ORG_ID = openai_org_id
    app.state.DEFAULT_MODEL = default_model
    app.state.ENVIRONMENT = environment
    app.state.VALIDATION_SCHEMA_PATH = validation_schema_path
    app.state.TOOLS_MANIFEST = tools_manifest_path

    # ------------------------------------------------------------
    # CORS
    # ------------------------------------------------------------
    origins_raw = os.getenv(
        "CORS_ALLOW_ORIGINS",
        "https://chat.openai.com,https://platform.openai.com",
    )
    allow_origins = [o.strip() for o in origins_raw.split(",") if o.strip()]

    methods_raw = os.getenv(
        "CORS_ALLOW_METHODS",
        "GET,POST,PUT,PATCH,DELETE,OPTIONS",
    )
    allow_methods = [m.strip() for m in methods_raw.split(",") if m.strip()]

    headers_raw = os.getenv("CORS_ALLOW_HEADERS", "*")
    allow_headers = [h.strip() for h in headers_raw.split(",") if h.strip()]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins or ["*"],
        allow_methods=allow_methods,
        allow_headers=allow_headers,
    )

    # ------------------------------------------------------------
    # Middleware stack: validation → orchestrator → routes
    # ------------------------------------------------------------
    app.add_middleware(SchemaValidationMiddleware)
    app.add_middleware(P4OrchestratorMiddleware)

    # ------------------------------------------------------------
    # Local meta routes
    # ------------------------------------------------------------

    @app.get("/")
    async def root():
        return {
            "object": "relay",
            "name": relay_name,
            "version": bifl_version,
            "environment": environment,
            "default_model": default_model,
            "openai_api_base": openai_api_base,
        }

    @app.get("/v1/health")
    async def health():
        """
        Lightweight health check for Render and external monitors.
        Does not call upstream OpenAI; just reports local status.
        """
        return {
            "object": "health",
            "status": "ok",
            "environment": environment,
            "default_model": default_model,
            "openai_api_base": openai_api_base,
        }

    @app.get("/schemas/openapi.yaml", include_in_schema=False)
    async def openapi_schema():
        """
        Serve the OpenAPI document used by ChatGPT Actions / Plugins.
        """
        schema_path = Path("schemas/openapi.yaml")
        if not schema_path.is_file():
            return JSONResponse(
                status_code=404,
                content={
                    "error": {
                        "message": "OpenAPI schema not found.",
                        "type": "not_found",
                    }
                },
            )
        return FileResponse(schema_path)

    # ------------------------------------------------------------
    # Routers (local endpoints)
    # ------------------------------------------------------------
    # /v1/tools and /v1/tools/{tool_id} — hosted tools registry
    app.include_router(tools_router)

    # Relay-focus /v1/* surfaces — locally handled (may still proxy upstream)
    app.include_router(responses_routes.router)
    app.include_router(conversations_routes.router)
    app.include_router(files_routes.router)
    app.include_router(vector_stores_routes.router)
    app.include_router(embeddings_routes.router)
    app.include_router(realtime_routes.router)
    app.include_router(models_routes.router)
    app.include_router(images_routes.router)
    app.include_router(videos_routes.router)
    app.include_router(actions_routes.router)

    # All other /v1/* paths fall back to P4Orchestrator + forward_openai_request.

    # ------------------------------------------------------------
    # Global error handlers
    # ------------------------------------------------------------
    register_error_handlers(app)

    return app


# FastAPI ASGI app object for uvicorn / Render
app = create_app()


# ------------------------------------------------------------
# Dev server entry point (local only)
# ------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8080"))
    reload_flag = os.getenv("RELAY_DEBUG", "false").lower() == "true"

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=reload_flag,
        log_level=os.getenv("LOG_LEVEL", "info"),
    )
