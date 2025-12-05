# app/main.py

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

    - Configures logging
    - Attaches middlewares (P4 orchestrator + relay auth)
    - Registers all routers (API + actions)
    """
    # Configure logging once, using global settings
    configure_logging(settings)

    app = FastAPI(
        title="ChatGPT Team Relay",
        version=getattr(settings, "APP_VERSION", "0.1.0"),
    )

    # Broad CORS – this is a relay, so UI clients may be anywhere.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Upstream orchestration middleware (adds model / API base context)
    app.add_middleware(P4OrchestratorMiddleware)

    # Relay auth middleware (Authorization: Bearer <RELAY_KEY>)
    app.add_middleware(RelayAuthMiddleware)

    # Routers: this is where app/api/routes.py is actually wired in.
    register_routes(app)

    return app


# Uvicorn / gunicorn entrypoint
app = create_app()
