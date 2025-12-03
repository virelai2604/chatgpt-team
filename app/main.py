# app/main.py
"""
main.py — ChatGPT Team Relay Entry Point
────────────────────────────────────────
Unified app bootstrap for the OpenAI-compatible relay.

Features:
  • Forwards /v1/* calls to the upstream OpenAI API via per-family routers.
  • Integrates JSON validation + orchestration middleware.
  • Registers /v1/tools from the hosted tools manifest.
  • Serves /schemas/openapi.yaml for ChatGPT Actions / Plugins.
  • Exposes /v1/health for Render health checks.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from app.core.config import settings
from app.middleware.validation import SchemaValidationMiddleware
from app.middleware.p4_orchestrator import P4OrchestratorMiddleware
from app.middleware.relay_auth import RelayAuthMiddleware
from app.utils.error_handler import register_exception_handlers
from app.routes.register_routes import register_routes


def create_app() -> FastAPI:
    # Load .env (no-op on Render where env vars are already injected)
    load_dotenv()

    relay_name = settings.RELAY_NAME
    bifl_version = os.getenv("BIFL_VERSION", "dev")

    app = FastAPI(
        title=relay_name,
        version=bifl_version,
        docs_url="/docs",
        openapi_url="/openapi.json",
    )

    # -------- CORS --------
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # -------- Relay auth --------
    if settings.RELAY_AUTH_ENABLED:
        relay_key = getattr(settings, "RELAY_KEY", "")
        app.add_middleware(RelayAuthMiddleware, relay_key=relay_key)

    # -------- P4 Orchestrator (AsyncOpenAI client on request.state) --------
    app.add_middleware(P4OrchestratorMiddleware)
        

    # -------- Schema validation middleware (logging + future hook) --------
    schema_path = Path("schemas/openapi.yaml")
    app.add_middleware(
        SchemaValidationMiddleware,
        schema_path=str(schema_path) if schema_path.is_file() else None,
    )

    # -------- Routes --------
    register_routes(app)

    # -------- Exception handlers (OpenAI-style error envelopes) --------
    register_exception_handlers(app)

    # -------- OpenAPI YAML for ChatGPT Actions / Plugins --------
    @app.get("/schemas/openapi.yaml", include_in_schema=False)
    async def get_openapi_yaml():
        if not schema_path.is_file():
            return JSONResponse(
                status_code=404,
                content={
                    "error": {
                        "message": "schemas/openapi.yaml not found",
                        "type": "invalid_request_error",
                    }
                },
            )
        return FileResponse(schema_path)

    return app


app = create_app()
