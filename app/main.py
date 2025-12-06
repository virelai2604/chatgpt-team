# app/main.py

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.utils.error_handler import register_exception_handlers
from app.middleware.p4_orchestrator import P4OrchestratorMiddleware
from app.middleware.relay_auth import RelayAuthMiddleware
from app.middleware.validation import ValidationMiddleware
from app.api.routes import router as api_router
from app.api.sse import router as sse_router
from app.api.tools_api import router as tools_router
from app.routes.register_routes import register_routes


def create_app() -> FastAPI:
    """
    Application factory for the ChatGPT Team Relay.

    Canonical wiring:

      - Core config:      app.core.config.Settings / get_settings()
      - Logging:          app.core.logging.configure_logging(settings)
      - Middleware:       P4 orchestrator, relay auth, validation, CORS
      - SDK /v1 routes:   app.api.routes (Responses, Embeddings, Images, Videos, Models)
      - SSE streaming:    app.api.sse
      - Tools manifest:   app.api.tools_api
      - Resource routes:  app.routes.register_routes (health, files, conversations, etc.)
    """
    settings = get_settings()

    # Initialise logging once for the entire relay (env-driven).
    configure_logging(settings)

    app = FastAPI(
        title=settings.project_name,
        version="0.1.0",
    )

    # ------------------------------------------------------------------
    # Middleware
    # ------------------------------------------------------------------
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],          # tighten for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(P4OrchestratorMiddleware)
    app.add_middleware(RelayAuthMiddleware)
    app.add_middleware(ValidationMiddleware)

    # Global error handlers (normalise upstream / internal failures)
    register_exception_handlers(app)

    # ------------------------------------------------------------------
    # Canonical /v1 API surface (SDK-based + SSE + tools)
    # ------------------------------------------------------------------
    app.include_router(api_router)   # /v1/responses, /v1/embeddings, /v1/images, /v1/videos, /v1/models
    app.include_router(sse_router)   # /v1/responses:stream
    app.include_router(tools_router) # /v1/tools

    # ------------------------------------------------------------------
    # Resource families under app/routes/*
    # (generic proxying via forward_openai_request + specialised endpoints)
    # ------------------------------------------------------------------
    register_routes(app)

    # Health is provided by app/routes/health.py:
    #   - GET /health
    #   - GET /v1/health
    #
    # No inline /health handler here; the router covers it.

    return app


# Uvicorn entrypoint
app = create_app()
