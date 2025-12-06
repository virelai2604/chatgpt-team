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
from .routes.register_routes import register_routes


def create_app() -> FastAPI:
    """
    Application factory for the ChatGPT Team Relay.

    Wires:
      - SDK-backed OpenAI endpoints (Responses / Embeddings / Images / Videos / Models)
      - SSE streaming endpoints for Responses
      - Tools manifest list
      - REST resource families (files, conversations, containers, batches, actions, vector stores)
      - Realtime HTTP + WS proxy
      - Health checks
    """
    settings = get_settings()
    # Use the configured log level from settings
    configure_logging(settings.log_level)

    app = FastAPI(
        title=settings.project_name,
        version="0.1.0",
    )

    # Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(P4OrchestratorMiddleware)
    app.add_middleware(RelayAuthMiddleware)
    app.add_middleware(ValidationMiddleware)

    # Error handlers
    register_exception_handlers(app)

    # Core SDK-based APIs
    app.include_router(api_router)

    # SSE streaming for Responses
    app.include_router(sse_router)

    # Tools manifest API
    app.include_router(tools_router)

    # Resource families (files, conversations, containers, batches, actions, vector stores),
    # Realtime, and Health (/health and /v1/health)
    register_routes(app)

    return app


app = create_app()
