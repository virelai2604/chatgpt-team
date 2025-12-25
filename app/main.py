from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as api_router
from app.api.sse import router as sse_router
from app.api.tools_api import router as tools_router
from app.core.config import get_settings
from app.middleware.p4_orchestrator import P4OrchestratorMiddleware
from app.middleware.relay_auth import RelayAuthMiddleware
from app.middleware.validation import ValidationMiddleware


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=getattr(settings, "RELAY_NAME", "ChatGPT Team Relay"),
        version="0.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
    )

    # Middlewares (order: last added runs first)
    app.add_middleware(P4OrchestratorMiddleware)

    # Always install RelayAuthMiddleware; it no-ops when RELAY_AUTH_ENABLED is false.
    app.add_middleware(RelayAuthMiddleware)

    app.add_middleware(ValidationMiddleware)

    # Routers
    app.include_router(sse_router)
    app.include_router(tools_router)
    app.include_router(api_router)

    return app


app = create_app()
