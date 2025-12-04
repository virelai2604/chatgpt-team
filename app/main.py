from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router as api_router
from app.core.config import settings
from app.middleware.p4_orchestrator import P4OrchestratorMiddleware
from app.middleware.relay_auth import RelayAuthMiddleware
from app.routes.register_routes import register_routes
from app.utils.error_handler import register_exception_handlers


def _split_csv(value: str) -> list[str]:
    """
    Utility to turn comma-separated env strings into clean lists.

    Example:
        "https://chat.openai.com, https://platform.openai.com"
        -> ["https://chat.openai.com", "https://platform.openai.com"]
    """
    return [item.strip() for item in value.split(",") if item.strip()]


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application for the ChatGPT Team Relay.
    """

    app = FastAPI(
        title=settings.RELAY_NAME,
        version="1.0.0",
    )

    # -------- CORS --------
    cors_origins = _split_csv(settings.CORS_ALLOW_ORIGINS)
    cors_methods = _split_csv(settings.CORS_ALLOW_METHODS)
    cors_headers = _split_csv(settings.CORS_ALLOW_HEADERS)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=cors_methods,
        allow_headers=cors_headers,
    )

    # -------- P4 orchestrator (OpenAI client + config) --------
    # This middleware centralizes OpenAI client config, streaming behavior,
    # timeouts, and naming. Routers simply call `forward_openai_request`.
    app.add_middleware(
        P4OrchestratorMiddleware,
        openai_api_base=str(settings.OPENAI_API_BASE),
        default_model=settings.DEFAULT_MODEL,
        realtime_model=settings.REALTIME_MODEL,
        enable_stream=settings.ENABLE_STREAM,
        chain_wait_mode=settings.CHAIN_WAIT_MODE,
        proxy_timeout=settings.PROXY_TIMEOUT,
        relay_timeout=settings.RELAY_TIMEOUT,
        relay_name=settings.RELAY_NAME,
    )

    # -------- Relay key auth (protects /v1/*, but not health) --------
    # RelayAuthMiddleware exempts `/health` and `/v1/health` internally.
    if settings.RELAY_AUTH_ENABLED:
        app.add_middleware(
            RelayAuthMiddleware,
            relay_key=settings.RELAY_KEY,
        )

    # -------- Routes & error handlers --------
    # Register all /v1 routers:
    #   - /health, /v1/health
    #   - /v1/responses, /v1/conversations, /v1/embeddings, /v1/models
    #   - /v1/files, /v1/images, /v1/videos, /v1/vector_stores
    #   - /v1/realtime/sessions
    #   - /v1/tools, /v1/actions/*
    register_routes(app)
    app.include_router(api_router)

    # Attach global exception handlers (OpenAI-style error envelopes, logging)
    register_exception_handlers(app)

    return app


app = create_app()

# Optional: enable `python -m app.main` direct execution for local dev.
if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.RELAY_HOST,
        port=8000,
        reload=True,
    )
