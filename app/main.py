# app/main.py

from __future__ import annotations

from fastapi import FastAPI

from app.api.routes import router as api_router
from app.api.sse import router as sse_router
from app.api.tools_api import router as tools_router
from app.core.config import get_settings, Settings
from app.middleware.p4_orchestrator import P4OrchestratorMiddleware
from app.middleware.relay_auth import RelayAuthMiddleware
from app.middleware.validation import ValidationMiddleware
from app.routes.register_routes import register_routes
from app.utils.error_handler import register_exception_handlers
from app.utils.logger import configure_logging


def create_app() -> FastAPI:
    settings: Settings = get_settings()

    # Configure logging once, then build the app.
    configure_logging(settings.log_level)

    app = FastAPI(
        title=settings.project_name,
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Global exception handlers
    register_exception_handlers(app)

    # Middleware stack
    app.add_middleware(RelayAuthMiddleware)
    app.add_middleware(ValidationMiddleware)
    app.add_middleware(P4OrchestratorMiddleware)

    # Canonical SDK-based routes (/v1/*)
    app.include_router(api_router)
    app.include_router(sse_router)
    app.include_router(tools_router)

    # Generic route families and health
    register_routes(app)

    return app


app = create_app()
