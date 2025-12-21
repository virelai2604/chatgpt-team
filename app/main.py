from __future__ import annotations

from typing import Callable, Dict

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


def _unique_id_factory() -> Callable[[APIRoute], str]:
    """
    Collision-resistant OpenAPI operationId generator.

    If two routes would otherwise generate the same operationId, we append _2, _3, ...
    This removes FastAPI duplicate operationId warnings even when duplicate routes exist.
    """
    seen: Dict[str, int] = {}

    def _gen(route: APIRoute) -> str:
        methods = "_".join(sorted(route.methods or []))
        path = (route.path_format or route.path).strip("/")
        path = path.replace("/", "_").replace("{", "").replace("}", "")
        name = route.name or getattr(route.endpoint, "__name__", "endpoint")

        base = f"{name}_{methods}_{path}".strip("_")
        n = seen.get(base, 0) + 1
        seen[base] = n
        return base if n == 1 else f"{base}_{n}"

    return _gen


def _get_bool_setting(settings: object, snake: str, upper: str, default: bool) -> bool:
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
        generate_unique_id_function=_unique_id_factory(),
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
        allow_credentials=settings.cors_allow_credentials,
    )

    relay_auth_enabled = _get_bool_setting(settings, "relay_auth_enabled", "RELAY_AUTH_ENABLED", True)
    if relay_auth_enabled:
        app.add_middleware(RelayAuthMiddleware)

    app.add_middleware(ValidationMiddleware)
    app.add_middleware(P4OrchestratorMiddleware)

    register_routes(app)
    app.include_router(tools_router)
    app.include_router(sse_router)

    register_exception_handlers(app)
    app.add_event_handler("shutdown", close_async_clients)
    return app


app = create_app()
