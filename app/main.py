"""
FastAPI application factory for the ChatGPT Team Relay.

This module constructs the FastAPI instance, configures logging, attaches
middleware, and registers all routers. It aligns the relay's behaviour
with the OpenAI platform APIs by using the orchestrator and auth middleware
and by including all API and tool routes.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import configure_logging
from app.middleware.p4_orchestrator import P4OrchestratorMiddleware
from app.middleware.relay_auth import RelayAuthMiddleware
from app.routes.register_routes import register_routes


def create_app() -> FastAPI:
    """
    Application factory for the ChatGPT Team Relay.

    Responsibilities:
    - Configure logging once using the relay settings.
    - Attach P4 orchestration and relay auth middleware.
    - Register all API and tool routes under the appropriate prefixes.

    Returns:
        A fully configured FastAPI application ready for Uvicorn or Gunicorn.
    """
    # Configure logging at startup. This call is intended to be idempotent.
    configure_logging(settings)

    app = FastAPI(
        title="ChatGPT Team Relay",
        version=getattr(settings, "APP_VERSION", "0.1.0"),
    )

    # Broad CORS – the relay may be called from various UI clients.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Attach the P4 orchestrator; this enriches request.state with an
    # OpenAI client and relay configuration used by downstream routes.
    app.add_middleware(P4OrchestratorMiddleware)

    # Relay authentication. If RELAY_AUTH_ENABLED is true, requests must
    # include Authorization: Bearer <RELAY_KEY>; otherwise this is a no-op.
    app.add_middleware(RelayAuthMiddleware)

    # Register all routers (OpenAI-style endpoints, tools, actions, fallback)
    register_routes(app)

    return app


# Uvicorn / Gunicorn entrypoint. ASGI servers will import "app".
app = create_app()
