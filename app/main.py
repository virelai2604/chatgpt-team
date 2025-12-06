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

    Canonical wiring:

    - /health, /v1/health:
        app.routes.health (mounted via register_routes)

    - Core REST families (generic HTTP proxy via forward_openai_request):
        /v1/files
        /v1/conversations
        /v1/containers
        /v1/batches
        /v1/actions
        /v1/vector_stores
        /v1/realtime/*

      (all mounted via register_routes)

    - Canonical SDK-backed OpenAI endpoints (Python SDK v2.x):
        /v1/responses
        /v1/embeddings
        /v1/images, /v1/images/generations
        /v1/videos
        /v1/models, /v1/models/{model_id}

      (from app.api.routes)

    - Streaming:
        /v1/responses:stream (from app.api.sse)

    - Tools:
        /v1/tools (from app.api.tools_api)
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

    # Resource routes (health + REST relay + realtime)
    register_routes(app)

    # SDK-based core OpenAI APIs
    app.include_router(api_router)

    # Streaming and tools
    app.include_router(sse_router)
    app.include_router(tools_router)

    return app


app = create_app()
