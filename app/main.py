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
    Application factory for the ChatGPT Team relay.

    Canonical wiring:

      - Shared config via app.core.config.get_settings()
      - Logging via app.utils.logger.configure_logging()
      - Middlewares: P4 orchestrator, relay auth, validation
      - SDK-based OpenAI endpoints under /v1 (Responses, Embeddings, Images, Videos, Models)
      - SSE streaming for Responses under /v1/responses:stream
      - Tools manifest under /v1/tools
      - Route families registered via app.routes.register_routes.register_routes()
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

    # Core SDK / OpenAI API routes
    app.include_router(api_router)       # /v1/* via OpenAI SDK & generic forward
    app.include_router(sse_router)       # /v1/responses:stream SSE
    app.include_router(tools_router)     # /v1/tools

    # Route-family wiring (files, containers, batches, realtime, health, etc.)
    register_routes(app)

    # NOTE: We no longer define an inline /health here.
    # /health and /v1/health are provided by app.routes.health.

    return app


# Global ASGI app for uvicorn and tests
app = create_app()
