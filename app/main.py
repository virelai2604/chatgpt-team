from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from app.core.config import settings
from app.middleware.p4_orchestrator import P4OrchestratorMiddleware
from app.middleware.relay_auth import RelayAuthMiddleware
from app.middleware.validation import SchemaValidationMiddleware
from app.routes.register_routes import register_routes
from app.utils.error_handler import register_exception_handlers
from app.utils.logger import setup_logging, relay_log

logger = logging.getLogger("chatgpt_team_relay")


def create_app() -> FastAPI:
    # Configure logging once at startup
    setup_logging()
    relay_log.info("ChatGPT Team Relay starting up")

    app = FastAPI(
        title=settings.RELAY_NAME,
        version="1.0.0",
        docs_url="/docs",
        redoc_url=None,
    )

    # ------------------------------------------------------------------
    # Global error handlers (OpenAI-style envelopes)
    # ------------------------------------------------------------------
    register_exception_handlers(app)

    # ------------------------------------------------------------------
    # CORS
    # ------------------------------------------------------------------
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins_list or ["*"],
        allow_credentials=True,
        allow_methods=settings.cors_allow_methods_list or ["*"],
        allow_headers=settings.cors_allow_headers_list or ["*"],
    )

    # ------------------------------------------------------------------
    # Middleware chain
    # ------------------------------------------------------------------
    # 1) Schema logging / future validation (PDF/OpenAPI)
    app.add_middleware(
        SchemaValidationMiddleware,
        schema_path=settings.VALIDATION_SCHEMA_PATH,
    )

    # 2) Relay auth (if RELAY_AUTH_ENABLED=true)
    app.add_middleware(RelayAuthMiddleware)

    # 3) Orchestration → decide local vs upstream OpenAI
    app.add_middleware(
        P4OrchestratorMiddleware,
        openai_api_base=settings.OPENAI_API_BASE,
        default_model=settings.DEFAULT_MODEL,
        enable_stream=settings.ENABLE_STREAM,
        chain_wait_mode=settings.CHAIN_WAIT_MODE,
        proxy_timeout=settings.PROXY_TIMEOUT,
        relay_timeout=settings.RELAY_TIMEOUT,
        # these extra kwargs are safely ignored by **_ in middleware __init__
        app_mode=settings.APP_MODE,
        environment=settings.ENVIRONMENT,
        tools_manifest=settings.TOOLS_MANIFEST,
        validation_schema_path=settings.VALIDATION_SCHEMA_PATH,
    )

    # ------------------------------------------------------------------
    # Routers (core OpenAI-compatible and relay-local)
    # NOTE: routers themselves already define /v1/... paths.
    #       Do NOT add another prefix="/v1" here, or you get /v1/v1/...
    # ------------------------------------------------------------------
    register_routes(app)

    # ------------------------------------------------------------------
    # Basic health + info
    # ------------------------------------------------------------------
    @app.get("/", include_in_schema=False)
    async def root() -> JSONResponse:
        return JSONResponse(
            {
                "name": settings.RELAY_NAME,
                "status": "ok",
                "mode": settings.APP_MODE,
                "environment": settings.ENVIRONMENT,
            }
        )

    @app.get("/health", include_in_schema=False)
    async def health() -> JSONResponse:
        return JSONResponse(
            {
                "status": "ok",
                "mode": settings.APP_MODE,
                "environment": settings.ENVIRONMENT,
            }
        )

    @app.get("/v1/health", include_in_schema=False)
    async def v1_health() -> JSONResponse:
        return JSONResponse(
            {
                "status": "ok",
                "mode": settings.APP_MODE,
                "environment": settings.ENVIRONMENT,
            }
        )

    # ------------------------------------------------------------------
    # Serve OpenAPI YAML at /openapi.yaml (for ai-plugin.json / Actions)
    # ------------------------------------------------------------------
    @app.get("/openapi.yaml", include_in_schema=False)
    async def openapi_yaml() -> FileResponse:
        """
        Serve the OpenAPI schema used by ChatGPT Actions / plugin manifest.
        """
        # project root = parent of the "app" package directory
        project_root = Path(__file__).resolve().parent.parent
        schema_path = project_root / "schemas" / "openapi.yaml"
        return FileResponse(schema_path)

    return app


app = create_app()
