# app/main.py

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import get_settings
from .core.logging import configure_logging
from .utils.error_handler import register_exception_handlers
from .middleware.p4_orchestrator import P4OrchestratorMiddleware
from .middleware.relay_auth import RelayAuthMiddleware
from .middleware.validation import ValidationMiddleware
from .routes.register_routes import register_routes
from .api.sse import router as sse_router
from .api.tools_api import router as tools_router


def create_app() -> FastAPI:
    """
    Application factory for the ChatGPT Team Relay.

    Canonical wiring:

      - Loads environment-driven Settings via app.core.config.get_settings.
      - Configures logging via app.core.logging.configure_logging(settings).
      - Adds P4 / auth / validation middleware layers.
      - Wires all REST resource families via app.routes.register_routes.register_routes(app).
      - Wires streaming Responses SSE under /v1/responses:stream.
      - Wires tools / manifest endpoints.

    This is the single entrypoint used by uvicorn and tests.
    """
    settings = get_settings()

    # Centralised logging configuration, bridged into app.utils.logger.
    configure_logging(settings)

    app = FastAPI(
        title=settings.project_name,
        version="0.1.0",
    )

    # CORS – permissive by default; tighten in production as needed.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # P4-style orchestration + auth + validation middleware stack.
    app.add_middleware(P4OrchestratorMiddleware)
    app.add_middleware(RelayAuthMiddleware)
    app.add_middleware(ValidationMiddleware)

    # Centralised exception handling.
    register_exception_handlers(app)

    # Canonical route registration for REST families (/v1/* plus /health).
    register_routes(app)

    # SSE streaming endpoint for Responses API (/v1/responses:stream).
    app.include_router(sse_router)

    # Tools / plugin metadata endpoints (e.g. /.well-known/ai-plugin.json, /v1/tools).
    app.include_router(tools_router)

    return app


# Uvicorn/tests entrypoint
app = create_app()
