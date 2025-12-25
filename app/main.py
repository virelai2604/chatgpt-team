from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.sse import router as sse_router
from app.api.tools_api import router as tools_router
from app.core.config import get_settings
from app.middleware.relay_auth import RelayAuthMiddleware
from app.routes.register_routes import register_routes

logger = logging.getLogger("relay")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="OpenAI-compatible Relay",
        version="1.0.0",
        docs_url=None,
        redoc_url=None,
        openapi_url="/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ALLOW_ORIGINS,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=settings.CORS_ALLOW_METHODS,
        allow_headers=settings.CORS_ALLOW_HEADERS,
    )

    app.add_middleware(RelayAuthMiddleware)

    register_routes(app)
    app.include_router(tools_router)
    app.include_router(sse_router)

    @app.middleware("http")
    async def _log_requests(request: Request, call_next):
        response = await call_next(request)
        try:
            logger.info("%s %s -> %s", request.method, request.url.path, response.status_code)
        except Exception:
            pass
        return response

    @app.get("/", include_in_schema=False)
    async def root():
        return {"status": "ok", "service": "openai-relay"}

    return app


app = create_app()
