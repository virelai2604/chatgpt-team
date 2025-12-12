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
from .routes import register_routes
from .api.sse import router as sse_router
from .api.tools_api import router as tools_router


def create_app() -> FastAPI:
    """
    Application factory for the ChatGPT Team relay.

    - Configures logging & CORS
    - Attaches orchestrator + auth + validation middleware
    - Registers global exception handlers
    - Wires all /v1/* routes via app.routes.register_routes
    - Adds SSE + tools endpoints
    """
    settings = get_settings()

    # Logging
    configure_logging(settings.log_level)

    app = FastAPI(
        title=settings.project_name,
        version="0.1.0",
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins or ["*"],
        allow_credentials=True,
        allow_methods=settings.cors_allow_methods or ["*"],
        allow_headers=settings.cors_allow_headers or ["*"],
    )

    # Middleware
    app.add_middleware(P4OrchestratorMiddleware)
    app.add_middleware(RelayAuthMiddleware)
    app.add_middleware(ValidationMiddleware)

    # Error handlers
    register_exception_handlers(app)

    # Core REST + SDK-driven /v1/* endpoints (includes /health, /v1/responses, /v1/embeddings, /v1/models, etc.)
    register_routes(app)

    # Additional API surfaces
    app.include_router(sse_router)
    app.include_router(tools_router)

    return app


app = create_app()
