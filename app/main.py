from __future__ import annotations

from fastapi import FastAPI

from app.api.sse import router as sse_router
from app.api.tools_api import router as tools_router
from app.core.config import get_settings, logger
from app.middleware.error_handler import ErrorHandlingMiddleware
from app.middleware.p4_orchestrator import P4OrchestratorMiddleware
from app.middleware.relay_auth import RelayAuthMiddleware
from app.routes.register_routes import register_routes


def _get_bool_setting(settings: object, snake: str, upper: str, default: bool) -> bool:
    if hasattr(settings, snake):
        return bool(getattr(settings, snake))
    if hasattr(settings, upper):
        return bool(getattr(settings, upper))
    return default


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="ChatGPT Team Relay",
        version="0.1.0",
        description="A relay service that forwards requests to OpenAI (with guardrails).",
    )

    # Order matters: error handling should wrap everything.
    app.add_middleware(ErrorHandlingMiddleware)
    app.add_middleware(P4OrchestratorMiddleware)

    # IMPORTANT:
    # Always install RelayAuthMiddleware so tests (and runtime) can toggle auth via settings.
    # check_relay_key() no-ops when RELAY_AUTH_ENABLED is false, so this remains safe.
    app.add_middleware(RelayAuthMiddleware)

    register_routes(app)

    # Also serve tools manifest + SSE tool endpoints (useful for ChatGPT Actions)
    app.include_router(tools_router)
    app.include_router(sse_router)

    relay_auth_enabled = _get_bool_setting(settings, "relay_auth_enabled", "RELAY_AUTH_ENABLED", True)
    logger.info(
        "App created",
        extra={
            "app_mode": getattr(settings, "APP_MODE", None),
            "relay_auth_enabled": relay_auth_enabled,
        },
    )

    return app


app = create_app()
