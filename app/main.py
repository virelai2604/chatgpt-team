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

# Core SDK-based /v1 APIs (responses, embeddings, images, videos, models)
from .api.routes import router as api_router  # type: ignore

# SSE streaming bridge for Responses
from .api.sse import router as sse_router  # type: ignore

# Tools manifest surface (/v1/tools)
from .api.tools_api import router as tools_router  # type: ignore

# Resource / proxy route families (/v1/files, /v1/batches, /v1/containers, etc.)
from .routes.register_routes import register_routes  # type: ignore


def create_app() -> FastAPI:
    """
    Application factory for the ChatGPT Team Relay.

    This wires:
      - Canonical SDK-based OpenAI endpoints under /v1  (app.api.routes)
      - Streaming Responses bridge under /v1            (app.api.sse)
      - Tools manifest under /v1/tools                  (app.api.tools_api)
      - Resource families and catch-all proxies         (app.routes.* via register_routes)
    """
    settings = get_settings()

    # Configure logging once, using the configured log level
    configure_logging(settings.log_level)

    app = FastAPI(
        title=settings.project_name,
        version="0.1.0",
        description="FastAPI relay for the OpenAI platform using the Python SDK.",
    )

    # CORS – permissive by default; tighten for production as needed.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Middleware stack (P4 orchestrator, auth, basic validation)
    app.add_middleware(P4OrchestratorMiddleware)
    app.add_middleware(RelayAuthMiddleware)
    app.add_middleware(ValidationMiddleware)

    # Centralised error handling including OpenAI API errors
    register_exception_handlers(app)

    # Canonical /v1 APIs
    app.include_router(api_router)
    app.include_router(sse_router)
    app.include_router(tools_router)

    # Route families: health, files, batches, containers, conversations,
    # vector stores, models, responses, embeddings, images, videos, realtime, etc.
    register_routes(app)

    return app


app = create_app()
