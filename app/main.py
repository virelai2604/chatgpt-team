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
    """
    Stable, unique OpenAPI operationIds.

    FastAPI can warn about duplicate operationId values when multiple endpoints
    resolve to the same auto-generated ID (common with catch-alls, alias routes,
    and multi-method handlers). We incorporate methods + path for uniqueness.
    """
    methods = "_".join(sorted(route.methods or []))
    path = (route.path_format or route.path).strip("/")
    path = path.replace("/", "_").replace("{", "").replace("}", "")
    name = route.name or getattr(route.endpoint, "__name__", "endpoint")
    return f"{name}_{methods}_{path}".strip("_")


def _get_bool_setting(settings: object, snake: str, upper: str, default: bool) -> bool:
    """
    BIFL compatibility helper: supports both snake_case and UPPERCASE config styles.
    """
    if hasattr(settings, snake):
        return bool(getattr(settings, snake))
    if hasattr(settings, upper):
        return bool(getattr(settings, upper))
    return default


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

    # Relay auth (config is UPPERCASE in app/core/config.py)
    relay_auth_enabled = _get_bool_setting(settings, "relay_auth_enabled", "RELAY_AUTH_ENABLED", True)
    if relay_auth_enabled:
        app.add_middleware(RelayAuthMiddleware)

    # Lightweight content-type validation (JSON/multipart enforcement)
    app.add_middleware(ValidationMiddleware)

    # Orchestrator middleware
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
