# app/main.py

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import get_settings
from .utils.logger import configure_logging
from .utils.error_handler import register_exception_handlers
from .middleware.p4_orchestrator import P4OrchestratorMiddleware
from .middleware.relay_auth import RelayAuthMiddleware
from .middleware.validation import ValidationMiddleware
from .api.routes import router as api_router
from .api.sse import router as sse_router
from .api.tools_api import router as tools_router
from .routes.health import router as health_router


def create_app() -> FastAPI:
    settings = get_settings()

    # Logging
    configure_logging(settings.log_level)

    app = FastAPI(
        title=settings.project_name,
        version="0.1.0",
    )

    # Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins or ["*"],
        allow_credentials=True,
        allow_methods=settings.cors_allow_methods or ["*"],
        allow_headers=settings.cors_allow_headers or ["*"],
    )
    app.add_middleware(P4OrchestratorMiddleware)
    app.add_middleware(RelayAuthMiddleware)
    app.add_middleware(ValidationMiddleware)

    # Error handlers
    register_exception_handlers(app)

    # API routes (versioned & tools)
    app.include_router(api_router)
    app.include_router(sse_router)
    app.include_router(tools_router)

    # Health routes (includes /health and /v1/health)
    app.include_router(health_router)

    return app


app = create_app()
