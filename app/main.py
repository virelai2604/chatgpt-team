# app/main.py

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.utils.logger import configure_logging
from app.utils.error_handler import register_exception_handlers
from app.middleware.p4_orchestrator import P4OrchestratorMiddleware
from app.middleware.relay_auth import RelayAuthMiddleware
from app.middleware.validation import ValidationMiddleware

from app.api.sse import router as sse_router
from app.api.tools_api import router as tools_router
from app.routes.register_routes import register_routes


def create_app() -> FastAPI:
    """
    Application factory for the ChatGPT Team Relay.

    Wires:
      - Core REST + SDK-based OpenAI routes under /v1 via app.routes.*
      - SSE streaming endpoints under /v1 via app.api.sse
      - Tools manifest endpoints under /v1 via app.api.tools_api
      - Orchestrator, relay auth, and validation middleware
    """
    settings = get_settings()

    # Initialise logging once for the whole process.
    # Uses LOG_LEVEL env var by default; settings.log_level acts as a hint.
    configure_logging(settings.log_level)

    app = FastAPI(
        title=settings.project_name,
        version="0.1.0",
        description="FastAPI relay for the OpenAI platform using the Python SDK.",
    )

    # CORS – allow typical browser/front-end access; tighten in production as needed.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # customise for your deployment if needed
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Core middlewares
    app.add_middleware(P4OrchestratorMiddleware)
    app.add_middleware(RelayAuthMiddleware)
    app.add_middleware(ValidationMiddleware)

    # Error handlers
    register_exception_handlers(app)

    # Resource routers (health, files, vectors, conversations, containers, batches, etc.)
    register_routes(app)

    # Streaming + tools
    app.include_router(sse_router)
    app.include_router(tools_router)

    # Optional bare /health for simple platform checks (distinct from /v1/health)
    @app.get("/health", tags=["health"])
    async def health_root() -> dict:
        return {"status": "ok"}

    return app


app = create_app()
