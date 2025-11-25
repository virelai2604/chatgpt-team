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
from app.api import tools_api as tools_routes
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

    # Global error handlers (OpenAI-style envelopes)
    register_exception_handlers(app)

    # --- CORS ---------------------------------------------------------------
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins_list or ["*"],
        allow_credentials=True,
        allow_methods=settings.cors_allow_methods_list or ["*"],
        allow_headers=settings.cors_allow_headers_list or ["*"],
    )

    # --- Middleware chain ---------------------------------------------------
    app.add_middleware(
        SchemaValidationMiddleware,
        schema_path=settings.VALIDATION_SCHEMA_PATH,
    )
    app.add_middleware(RelayAuthMiddleware)
    app.add_middleware(
        P4OrchestratorMiddleware,
        openai_api_base=settings.OPENAI_API_BASE,
        default_model=settings.DEFAULT_MODEL,
        realtime_model=settings.REALTIME_MODEL,
        enable_stream=settings.ENABLE_STREAM,
        chain_wait_mode=settings.CHAIN_WAIT_MODE,
        proxy_timeout=settings.PROXY_TIMEOUT,
        relay_timeout=settings.RELAY_TIMEOUT,
        relay_name=settings.RELAY_NAME,
    )

    # --- Routers ------------------------------------------------------------
    app.include_router(models_routes.router, prefix="/v1", tags=["models"])
    app.include_router(responses_routes.router, prefix="/v1", tags=["responses"])
    app.include_router(embeddings_routes.router, prefix="/v1", tags=["embeddings"])
    app.include_router(files_routes.router, prefix="/v1", tags=["files"])
    app.include_router(vector_stores_routes.router, prefix="/v1", tags=["vector_stores"])
    app.include_router(conversations_routes.router, prefix="/v1", tags=["conversations"])
    app.include_router(images_routes.router, prefix="/v1", tags=["images"])
    app.include_router(videos_routes.router, prefix="/v1", tags=["videos"])
    app.include_router(realtime_routes.router, prefix="/v1", tags=["realtime"])
    app.include_router(actions_routes.router, prefix="/relay", tags=["relay"])
    app.include_router(tools_routes.router, prefix="/v1", tags=["tools"])

    # --- Basic health + info -----------------------------------------------

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

    # Serve OpenAPI YAML at /openapi.yaml (for ai-plugin.json)
    @app.get("/openapi.yaml", include_in_schema=False)
    async def openapi_yaml() -> FileResponse:
        """
        Serve the OpenAPI schema used by ChatGPT Actions / plugin manifest.
        """
        root_dir = Path(__file__).resolve().parent.parent
        schema_path = root_dir / "openapi.yaml"
        return FileResponse(schema_path)

    return app


app = create_app()
