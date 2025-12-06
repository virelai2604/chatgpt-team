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
from app.routes.register_routes import register_routes
from app.api.sse import router as sse_router
from app.api.tools_api import router as tools_router


def create_app() -> FastAPI:
    """
    Application factory for the ChatGPT Team Relay.

    This wires:
    - Settings & logging
    - Core middleware (P4 orchestrator, relay auth, validation)
    - Canonical route families via register_routes(app)
    - SSE streaming and tools manifest endpoints
    """
    settings = get_settings()

    # Centralised logging configuration (bridged via app.core.logging)
    configure_logging(settings)

    app = FastAPI(
        title=settings.project_name,
        version="0.1.0",
    )

    # CORS – permissive by default for demo/agentic use; tighten in production.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Core relay middleware stack
    app.add_middleware(P4OrchestratorMiddleware)
    app.add_middleware(RelayAuthMiddleware)
    app.add_middleware(ValidationMiddleware)

    # Error handlers
    register_exception_handlers(app)

    # Canonical route families (health, files, containers, batches, vector_stores,
    # responses, embeddings, images, videos, models, realtime, etc.)
    register_routes(app)

    # SSE streaming responses and tools manifest under /v1
    app.include_router(sse_router)
    app.include_router(tools_router)

    # Optional simple root health – tests use /v1/health, but this is convenient
    @app.get("/health", tags=["health"])
    async def health_root() -> dict:
        return {"status": "ok"}

    return app


# Uvicorn / ASGI entrypoint
app = create_app()
