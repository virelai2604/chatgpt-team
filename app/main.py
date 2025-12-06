# app/main.py

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import get_settings
from .core.logging import configure_logging  # <- bridge module
from .utils.error_handler import register_exception_handlers
from .middleware.p4_orchestrator import P4OrchestratorMiddleware
from .middleware.relay_auth import RelayAuthMiddleware
from .middleware.validation import ValidationMiddleware
from .api.routes import router as api_router
from .api.sse import router as sse_router
from .api.tools_api import router as tools_router


def create_app() -> FastAPI:
    settings = get_settings()

    # Initialise logging once, based on environment / LOG_LEVEL.
    configure_logging(settings)

    app = FastAPI(
        title=settings.project_name,
        version="0.1.0",
    )

    # CORS – keep permissive for now; tighten for production.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # P4 / relay middleware stack
    app.add_middleware(P4OrchestratorMiddleware)
    app.add_middleware(RelayAuthMiddleware)
    app.add_middleware(ValidationMiddleware)

    # Error handlers (OpenAI errors, validation, generic 500s)
    register_exception_handlers(app)

    # Core API routers
    app.include_router(api_router)
    app.include_router(sse_router)
    app.include_router(tools_router)

    return app


app = create_app()
