from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.sse import router as sse_router
from .api.tools_api import router as tools_router
from .core.config import get_settings
from .core.http_client import close_async_clients
from .middleware.p4_orchestrator import P4OrchestratorMiddleware
from .middleware.relay_auth import RelayAuthMiddleware
from .middleware.validation import ValidationMiddleware
from .routes.register_routes import register_routes
from .utils.error_handler import register_exception_handlers
from .utils.logger import configure_logging


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(title=settings.project_name)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
        allow_credentials=settings.cors_allow_credentials,
    )

    # Auth guard (server-side relay key)
    app.add_middleware(RelayAuthMiddleware)

    # Validation middleware (optional)
    app.add_middleware(ValidationMiddleware)

    # Orchestrator middleware (optional)
    app.add_middleware(P4OrchestratorMiddleware)

    register_routes(app)
    app.include_router(tools_router)
    app.include_router(sse_router)
    register_exception_handlers(app)

    app.add_event_handler("shutdown", close_async_clients)
    return app


app = create_app()
