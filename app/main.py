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
from .api.sse import router as sse_router
from .api.tools_api import router as tools_router
from .routes import register_routes


def create_app() -> FastAPI:
    """
    Application factory for the ChatGPT Team Relay.

    Wires:
      - Core OpenAI relay routes under /v1 (via app.routes.*)
      - SSE streaming routes under /v1/responses:stream
      - Tools manifest routes under /v1/tools/*
    """
    settings = get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(
        title=settings.project_name,
        version="0.1.0",
    )

    # CORS – allow typical browser/front-end access; tighten in production as needed.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # P4 orchestration + auth + validation
    app.add_middleware(P4OrchestratorMiddleware)
    app.add_middleware(RelayAuthMiddleware)
    app.add_middleware(ValidationMiddleware)

    # Error handlers
    register_exception_handlers(app)

    # SSE + Tools routes
    app.include_router(sse_router)
    app.include_router(tools_router)

    # All resource /v1/* and health routes
    register_routes(app)

    return app


app = create_app()
