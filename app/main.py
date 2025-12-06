# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.utils.logger import configure_logging
from app.utils.error_handler import register_exception_handlers
from app.middleware.p4_orchestrator import P4OrchestratorMiddleware
from app.middleware.relay_auth import RelayAuthMiddleware
from app.middleware.validation import ValidationMiddleware
from app.routes.register_routes import register_routes
from app.api.routes import router as api_router
from app.api.sse import router as sse_router
from .api.tools_api import router as tools_router


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging()

    app = FastAPI(
        title=settings.project_name,
        version="0.1.0",
    )

    # Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(P4OrchestratorMiddleware)
    app.add_middleware(RelayAuthMiddleware)
    app.add_middleware(ValidationMiddleware)

    # Error handlers
    register_exception_handlers(app)

    # Route families under app.routes.*
    register_routes(app)

    # SDK/OpenAI proxy + streaming
    app.include_router(api_router)
    app.include_router(sse_router)
    app.include_router(tools_router)

    return app


app = create_app()
