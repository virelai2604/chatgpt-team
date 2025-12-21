from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute

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


def _generate_unique_operation_id(route: APIRoute) -> str:
    """Generate stable, unique OpenAPI operationIds.

    FastAPI can emit 'Duplicate Operation ID' warnings when multiple routes share
    the same auto-generated operationId (e.g., legacy aliases, catch-all routes,
    or GET/HEAD overlaps). This generator incorporates HTTP method(s) and path to
    ensure uniqueness while remaining deterministic.
    """
    methods = "_".join(sorted(route.methods or []))
    path = (route.path_format or route.path).replace("/", "_").replace("{", "").replace("}", "")
    name = route.name or getattr(route.endpoint, "__name__", "endpoint")
    return f"{name}_{methods}_{path}".strip("_")


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(
        title=settings.project_name,
        generate_unique_id_function=_generate_unique_operation_id,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
        allow_credentials=settings.cors_allow_credentials,
    )

    # Relay auth (optional)
    if settings.relay_auth_enabled:
        app.add_middleware(RelayAuthMiddleware)

    # Request validation (optional, but recommended for predictable upstream forwarding)
    if settings.validation_enabled:
        app.add_middleware(ValidationMiddleware)

    # Orchestrator middleware (optional)
    app.add_middleware(P4OrchestratorMiddleware)

    # Routes
    register_routes(app)
    app.include_router(tools_router)
    app.include_router(sse_router)

    # Error handlers
    register_exception_handlers(app)

    # Cleanup
    app.add_event_handler("shutdown", close_async_clients)

    return app


app = create_app()
