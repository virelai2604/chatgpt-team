"""
main.py — ChatGPT Team Relay Entry Point
────────────────────────────────────────
Unified app bootstrap for the OpenAI-compatible relay.

Focus:
  • Relay-focus surfaces handled locally:
      - Responses, Conversations, Files, Vector Stores, Embeddings,
        Realtime, Models, Images, Videos, Actions, Tools.
  • /v1/tools is a local tools registry for introspection.
  • Everything else under /v1/* is orchestrated and generally forwarded
    to OpenAI via P4OrchestratorMiddleware → forward_openai_request.

Configuration:
  • Runtime / environment come from env or Render dashboard:
      - APP_MODE, ENVIRONMENT
      - OPENAI_API_BASE, OPENAI_API_KEY
      - DEFAULT_MODEL
      - OPENAI_ASSISTANTS_BETA, OPENAI_REALTIME_BETA
      - CORS_* settings, RELAY_KEY, etc.

Health:
  • /health      — root health for E2E tests and Render checks.
  • /v1/health   — versioned health under the /v1 namespace.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from app.core.config import settings
from app.middleware.p4_orchestrator import P4OrchestratorMiddleware
from app.middleware.validation import SchemaValidationMiddleware
from app.middleware.relay_auth import RelayAuthMiddleware
from app.utils.error_handler import register_exception_handlers
from app.utils.logger import setup_logging
from app.routes.register_routes import register_routes

logger = logging.getLogger("chatgpt_team_relay")


def create_app() -> FastAPI:
    """
    Create the FastAPI application and attach middleware / routes.

    The goal is to keep this file very small and stable; the heavy
    lifting of routing and OpenAI orchestration happens in:
      • app.routes.register_routes.register_routes
      • app.middleware.p4_orchestrator.P4OrchestratorMiddleware
    """
    # Initialize structured logging first
    setup_logging()
    logger.info("Starting ChatGPT Team Relay app", extra={"path": "startup"})

    app = FastAPI(
        title=settings.RELAY_NAME,
        version=getattr(settings, "APP_VERSION", "1.0.0"),
        docs_url=None if settings.APP_MODE == "production" else "/docs",
        openapi_url=None if settings.APP_MODE == "production" else "/openapi.json",
    )

    # ------------------------------------------------------------------
    # Global error handlers (OpenAI-style error envelopes)
    # ------------------------------------------------------------------
    register_exception_handlers(app)

    # ------------------------------------------------------------------
    # 1) JSON schema validation
    # ------------------------------------------------------------------
    app.add_middleware(SchemaValidationMiddleware)

    # ------------------------------------------------------------------
    # 2) CORS
    # ------------------------------------------------------------------
    allow_origins = [
        origin.strip()
        for origin in settings.CORS_ALLOW_ORIGINS.split(",")
        if origin.strip()
    ]
    allow_methods = [
        method.strip()
        for method in settings.CORS_ALLOW_METHODS.split(",")
        if method.strip()
    ]
    allow_headers = [
        header.strip()
        for header in settings.CORS_ALLOW_HEADERS.split(",")
        if header.strip()
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins or ["*"],
        allow_methods=allow_methods or ["*"],
        allow_headers=allow_headers or ["*"],
        allow_credentials=True,
    )

    # ------------------------------------------------------------------
    # 3) Central RELAY_KEY gate (Auth middleware)
    # ------------------------------------------------------------------
    app.add_middleware(RelayAuthMiddleware)

    # ------------------------------------------------------------------
    # 4) P4 orchestrator: local vs upstream OpenAI
    # ------------------------------------------------------------------
    app.add_middleware(
        P4OrchestratorMiddleware,
        openai_api_base=settings.OPENAI_API_BASE,
        openai_api_key=settings.OPENAI_API_KEY,
        default_model=settings.DEFAULT_MODEL,
        assistants_beta=settings.OPENAI_ASSISTANTS_BETA,
        realtime_beta=settings.OPENAI_REALTIME_BETA,
        enable_stream=settings.ENABLE_STREAM,
        chain_wait_mode=settings.CHAIN_WAIT_MODE,
        app_mode=settings.APP_MODE,
        environment=settings.ENVIRONMENT,
        tools_manifest=settings.TOOLS_MANIFEST,
        validation_schema_path=settings.VALIDATION_SCHEMA_PATH,
        proxy_timeout=settings.PROXY_TIMEOUT,
        relay_timeout=settings.RELAY_TIMEOUT,
    )

    # ------------------------------------------------------------------
    # 5) Routes under /v1/*
    # ------------------------------------------------------------------
    register_routes(app)

    # ------------------------------------------------------------------
    # 6) Health endpoints (stay public)
    # ------------------------------------------------------------------
    def _health_payload() -> dict[str, Any]:
        return {
            "status": "ok",
            "relay_name": settings.RELAY_NAME,
            "environment": settings.ENVIRONMENT,
            "app_mode": settings.APP_MODE,
        }

    @app.get("/health")
    async def root_health() -> dict[str, Any]:
        return _health_payload()

    @app.get("/v1/health")
    async def v1_health() -> dict[str, Any]:
        return _health_payload()

    # ------------------------------------------------------------------
    # 7) Fallback for uncaught exceptions (extra guard)
    # ------------------------------------------------------------------
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:  # type: ignore[override]
        logger.exception("Unhandled exception", extra={"path": request.url.path})
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "message": "Internal server error",
                    "type": "internal_error",
                }
            },
        )

    return app


app = create_app()
