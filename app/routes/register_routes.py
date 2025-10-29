# ==========================================================
# app/routes/register_routes.py — Ground Truth Router Registry
# ==========================================================
from fastapi import FastAPI

# ---- Import all route modules ----
from app.routes import (
    relay_status,        # /health
    openapi_yaml,        # /v1/openapi.yaml
    responses,           # /v1/responses + input_tokens + tools
    models,              # /v1/models
    files,               # /v1/files
    vector_stores,       # /v1/vector_stores
    conversations,       # /v1/conversations
    realtime             # /v1/realtime/sessions
)

# Import the catch-all proxy LAST
from app.api import passthrough_proxy


# ==========================================================
# ROUTER REGISTRATION FUNCTION
# ==========================================================
def register_routes(app: FastAPI):
    """
    Mount all routers to the FastAPI app.
    The ordering ensures specific routes override generic proxy handlers.
    """

    # ---- System / meta endpoints ----
    app.include_router(relay_status.router, prefix="")          # /health
    app.include_router(openapi_yaml.router, prefix="")          # /v1/openapi.yaml

    # ---- Core OpenAI API mirrors ----
    app.include_router(models.router, prefix="")                # /v1/models
    app.include_router(files.router, prefix="")                 # /v1/files
    app.include_router(vector_stores.router, prefix="")         # /v1/vector_stores
    app.include_router(conversations.router, prefix="")         # /v1/conversations
    app.include_router(responses.router, prefix="")             # /v1/responses (+tools)
    app.include_router(realtime.router, prefix="")              # /v1/realtime/sessions

    # ---- Fallback / passthrough proxy ----
    app.include_router(passthrough_proxy.router, prefix="")     # Catch-all for other /v1/* routes

    # ---- Root convenience route ----
    @app.get("/", tags=["Meta"])
    async def root():
        """
        Returns basic relay info and pointers to documentation.
        """
        return {
            "service": "ChatGPT Team Relay (Cloudflare / Render)",
            "status": "running",
            "version": "Ground Truth Edition v2025.10",
            "docs": "/docs",
            "openapi_spec": "/v1/openapi.yaml",
            "health": "/health",
            "upstream": "https://api.openai.com",
        }

    return app
