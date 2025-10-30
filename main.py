# ==========================================================
# main.py — ChatGPT Team Relay (Ground Truth Edition)
# ==========================================================
"""
Main FastAPI entrypoint for the ChatGPT Team Relay.
Implements the Ground Truth Edition v2025.10 — fully OpenAI-compatible API mirror.
This file wires together routes, middleware, and the universal passthrough proxy.
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ==========================================================
# Route imports
# ==========================================================
# Core OpenAI-compatible routes
from app.routes.models import router as models_router
from app.routes.files import router as files_router
from app.routes.vector_stores import router as vector_stores_router
from app.routes.responses import router as responses_router
from app.routes.realtime import router as realtime_router

# Catch-all fallback proxy — must be last
from app.api.passthrough_proxy import router as passthrough_router

# Error handling utilities
from app.utils.error_handler import register_error_handlers


# ==========================================================
# App Initialization
# ==========================================================
logging.basicConfig(level=logging.INFO)
app = FastAPI(
    title="ChatGPT Team Relay API",
    description="Ground Truth compliant OpenAI-compatible relay (v2025.10).",
    version="2025.10",
)

# CORS Configuration
# Matches OpenAI SDK defaults: fully permissive for public relay endpoints
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================================
# Route Registration
# ==========================================================
# Order matters — specific routes first, catch-all last.
app.include_router(models_router)         # /v1/models
app.include_router(files_router)          # /v1/files
app.include_router(vector_stores_router)  # /v1/vector_stores
app.include_router(responses_router)      # /v1/responses (+tools)
app.include_router(realtime_router)       # /v1/realtime/sessions

# 👇 Must be registered last: fallback proxy to OpenAI
app.include_router(passthrough_router)    # /v1/{path:path}


# ==========================================================
# Error Handling
# ==========================================================
app = register_error_handlers(app)


# ==========================================================
# Root Healthcheck
# ==========================================================
@app.get("/", tags=["Meta"])
async def root():
    """
    Relay root endpoint.
    Returns relay service metadata and documentation pointers.
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


# ==========================================================
# Health Endpoint (explicit)
# ==========================================================
@app.get("/health", tags=["Health"])
async def healthcheck():
    return {"status": "ok", "version": "2025.10"}


# ==========================================================
# Run (local only)
# ==========================================================
# Example:
#   uvicorn app.main:app --reload --port 8080
# ==========================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8080, reload=True)
