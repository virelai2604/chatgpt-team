# app/main.py

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import get_settings
from .middleware.p4_orchestrator import P4OrchestratorMiddleware
from .middleware.relay_auth import RelayAuthMiddleware
from .middleware.validation import ValidationMiddleware
from .utils.error_handler import register_exception_handlers
from .utils.logger import configure_logging, get_logger
from .routes.register_routes import register_routes
from .api.sse import router as sse_router
from .api.tools_api import router as tools_router

logger = get_logger(__name__)


def create_app() -> FastAPI:
    """
    Application factory for the ChatGPT-Team relay.

    - Loads settings
    - Configures logging
    - Registers middleware & exception handlers
    - Mounts all route families under /v1 via register_routes(app)
    - Adds SSE and tools routers.
    """
    settings = get_settings()

    # Configure root logging
    configure_logging(settings.LOG_LEVEL)
    logger.info("Starting ChatGPT-Team relay in %s mode", settings.APP_MODE)

    app = FastAPI(
        title="ChatGPT-Team Relay",
        description="FastAPI relay in front of OpenAI platform API.",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # CORS (relaxed by default; tighten in production as needed)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ALLOW_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception handlers
    register_exception_handlers(app)

    # Middleware stack
    app.add_middleware(P4OrchestratorMiddleware)
    if settings.RELAY_AUTH_ENABLED:
        app.add_middleware(RelayAuthMiddleware)
    app.add_middleware(ValidationMiddleware)

    # Mount all route families (health, models, files, embeddings, etc.)
    register_routes(app)

    # SSE + tools special endpoints
    app.include_router(sse_router)
    app.include_router(tools_router)

    return app


# Uvicorn entrypoint
app: FastAPI = create_app()
