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

This file is designed to be stable and minimal — configuration lives in
env/.env, routing lives in register_routes.py, and the OpenAI behavior
follows the official OpenAI API reference.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from starlette.requests import Request
from starlette.staticfiles import StaticFiles

# FIXED: register_routes lives in app/routes/register_routes.py
from app.routes.register_routes import register_routes
from app.middleware.validation import SchemaValidationMiddleware
from app.middleware.p4_orchestrator import P4OrchestratorMiddleware

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR.parent / ".env"

logger = logging.getLogger("relay.main")


def _load_dotenv_if_present() -> None:
    """Load .env if present (simple, no external dependency)."""
    if not ENV_PATH.is_file():
        return
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def create_app() -> FastAPI:
    # Load .env early
    _load_dotenv_if_present()

    app_mode = os.getenv("APP_MODE", "local")
    environment = os.getenv("ENVIRONMENT", "local")
    openai_api_base = os.getenv("OPENAI_API_BASE", "https://api.openai.com")
    default_model = os.getenv("DEFAULT_MODEL", "gpt-4.1-mini")

    logger.info(
        "Starting ChatGPT Team Relay (APP_MODE=%s, ENVIRONMENT=%s, OPENAI_API_BASE=%s, DEFAULT_MODEL=%s)",
        app_mode,
        environment,
        openai_api_base,
        default_model,
    )

    app = FastAPI(
        title="ChatGPT Team Relay",
        version="1.0.0",
        description="OpenAI-compatible relay for ChatGPT Team / P4 agentic workflows.",
        docs_url=None,
        redoc_url=None,
        openapi_url="/schemas/openapi.json",
    )

    # CORS – allow typical frontends to talk to this relay
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )

    # Validation middleware – schema checks, logging, etc.
    app.add_middleware(SchemaValidationMiddleware)

    # P4 Orchestrator – handles /v1/* fallback and OpenAI proxy logic.
    app.add_middleware(P4OrchestratorMiddleware)

    # Static for .well-known metadata (ChatGPT Actions, etc.)
    well_known_dir = BASE_DIR / ".well-known"
    if well_known_dir.is_dir():
        app.mount("/.well-known", StaticFiles(directory=str(well_known_dir)), name="well_known")

    # Root health / info
    @app.get("/", response_class=PlainTextResponse, include_in_schema=False)
    async def root() -> str:
        return "ChatGPT Team Relay is running."

    @app.get("/v1/health", include_in_schema=True)
    async def health() -> Dict[str, Any]:
        return {
            "status": "ok",
            "app_mode": app_mode,
            "environment": environment,
            "openai_api_base": openai_api_base,
            "default_model": default_model,
        }

    # OpenAPI YAML export (optional)
    @app.get("/schemas/openapi.yaml", include_in_schema=False)
    async def openapi_yaml(request: Request) -> PlainTextResponse:
        # Generate JSON, then naive convert to YAML-ish.
        # This is good enough for local inspection / tests.
        openapi = app.openapi()
        try:
            import yaml  # type: ignore
        except Exception:
            # Fallback: just return JSON as text if PyYAML is not installed.
            import json

            return PlainTextResponse(json.dumps(openapi, indent=2))
        yaml_str = yaml.dump(openapi, sort_keys=False)
        return PlainTextResponse(yaml_str)

    # Central route registration
    register_routes(app)

    # Basic error handler so we return JSON consistently
    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled error: %s", exc)
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
