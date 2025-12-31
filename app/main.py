from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.sse import actions_router as sse_actions_router
from app.api.sse import router as sse_router
from app.api.tools_api import router as tools_router
from app.core.config import get_settings
from app.middleware.relay_auth import RelayAuthMiddleware
from app.routes.register_routes import register_routes
from app.utils.logger import relay_log as logger


def _get_bool_setting(value: object, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        v = value.strip().lower()
        if v in {"1", "true", "yes", "on"}:
            return True
        if v in {"0", "false", "no", "off"}:
            return False
    return default


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="chatgpt-team-relay",
        version="0.1.0",
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ALLOW_ORIGINS,
        allow_methods=settings.CORS_ALLOW_METHODS,
        allow_headers=settings.CORS_ALLOW_HEADERS,
        allow_credentials=_get_bool_setting(settings.CORS_ALLOW_CREDENTIALS, default=True),
    )

    # Always install relay auth middleware.
    # Whether it enforces auth is controlled at request-time (settings flags),
    # which is required for tests that monkeypatch settings without rebuilding the app.
    app.add_middleware(RelayAuthMiddleware)
    if getattr(settings, "RELAY_AUTH_ENABLED", False) and getattr(settings, "RELAY_KEY", ""):
        logger.info("Relay auth enabled (RELAY_AUTH_ENABLED=true).")
    else:
        logger.info("Relay auth disabled (RELAY_AUTH_ENABLED=false or RELAY_KEY missing).")

    # Register all route modules
    register_routes(app)

    # Tool manifest / helper endpoints
    app.include_router(tools_router)

    # SSE streaming endpoints (non-Actions + Actions wrapper)
    app.include_router(sse_router)
    app.include_router(sse_actions_router)

    return app


app = create_app()
