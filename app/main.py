# app/main.py

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.middleware.p4_orchestrator import P4OrchestratorMiddleware
from app.middleware.relay_auth import RelayAuthMiddleware
from app.routes.register_routes import register_routes
from app.utils.error_handler import register_exception_handlers


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


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
if settings.RELAY_AUTH_ENABLED:
    app.add_middleware(
        RelayAuthMiddleware,
        relay_key=settings.RELAY_KEY,
    )

# -------- Routes & error handlers --------
register_routes(app)
register_exception_handlers(app)
