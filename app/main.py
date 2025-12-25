import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.sse import create_sse_app
from app.core.config import get_settings
from app.middleware.p4_orchestrator import P4OrchestratorMiddleware
from app.middleware.relay_auth import RelayAuthMiddleware
from app.routes.register_routes import register_routes
from app.utils.logger import configure_logging


def _get_bool_setting(settings, snake: str, upper: str, default: bool) -> bool:
    if hasattr(settings, snake):
        v = getattr(settings, snake)
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            return v.strip().lower() in {"1", "true", "yes", "on"}

    if hasattr(settings, upper):
        v = getattr(settings, upper)
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            return v.strip().lower() in {"1", "true", "yes", "on"}

    return default


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings)

    enable_stream = _get_bool_setting(settings, "enable_stream", "ENABLE_STREAM", True)

    app = FastAPI(
        title="ChatGPT Team Relay",
        version=os.getenv("RELAY_VERSION", "0.0.0"),
        docs_url=None,
        redoc_url=None,
        openapi_url="/openapi.json",
    )

    # Orchestrator (logging / request context)
    app.add_middleware(P4OrchestratorMiddleware)

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # IMPORTANT:
    # Always install RelayAuthMiddleware so tests can toggle RELAY_AUTH_ENABLED via monkeypatch
    # even if the app was created while RELAY_AUTH_ENABLED=false.
    #
    # The middleware itself is a no-op when RELAY_AUTH_ENABLED is false.
    app.add_middleware(RelayAuthMiddleware)

    # Routes
    register_routes(app)

    # SSE mounting (non-actions clients)
    if enable_stream:
        app.mount("/v1/responses:stream", create_sse_app())

    return app


app = create_app()
