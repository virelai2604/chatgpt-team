# app/main.py

from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.middleware.p4_orchestrator import P4OrchestratorMiddleware
from app.middleware.relay_auth import RelayAuthMiddleware
from app.middleware.validation import SchemaValidationMiddleware
from app.routes.register_routes import register_routes
from app.utils.error_handler import register_exception_handlers
from app.utils.logger import setup_logging

logger = logging.getLogger("relay")


def create_app() -> FastAPI:
    setup_logging()

    app = FastAPI(
        title="ChatGPT Team Relay",
        version="1.0.0",
        docs_url=None,
        redoc_url=None,
        openapi_url="/openapi.json",
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins_list(),
        allow_credentials=True,
        allow_methods=settings.cors_allow_methods_list(),
        allow_headers=settings.cors_allow_headers_list(),
    )

    # Middlewares
    app.add_middleware(
        RelayAuthMiddleware,
        relay_key=settings.RELAY_KEY,
    )

    app.add_middleware(
        P4OrchestratorMiddleware,
        openai_api_base=str(settings.OPENAI_API_BASE),
        default_model=settings.DEFAULT_MODEL,
        realtime_model=settings.REALTIME_MODEL,
        relay_name=settings.RELAY_NAME,
    )

    app.add_middleware(SchemaValidationMiddleware)

    # Routes & error handlers
    register_routes(app)
    register_exception_handlers(app)

    logger.info(
        "Application initialised",
        extra={
            "relay_name": settings.RELAY_NAME,
            "environment": "production",
            "default_model": settings.DEFAULT_MODEL,
            "realtime_model": settings.REALTIME_MODEL,
        },
    )

    return app


app = create_app()


# For tests that introspect basic app info
def relay_info() -> Dict[str, Any]:
    return {
        "relay_name": settings.RELAY_NAME,
        "default_model": settings.DEFAULT_MODEL,
        "realtime_model": settings.REALTIME_MODEL,
        "openai_api_base": str(settings.OPENAI_API_BASE),
    }
