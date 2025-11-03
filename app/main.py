"""
main.py — ChatGPT Team Relay Entry Point
────────────────────────────────────────────────────────────
Fully OpenAI-compatible FastAPI relay aligned with:
  • openai-python SDK v2.61
  • openai-node SDK v6.7.0
  • Ground Truth API Reference (2025-10)

Features:
  • Middleware orchestration (SchemaValidation + P4)
  • Route auto-registration (/v1/*)
  • CORS for plugin/browser compatibility
  • Health + OpenAPI discovery routes
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from app.middleware.p4_orchestrator import P4OrchestratorMiddleware
from app.middleware.validation import SchemaValidationMiddleware
from app.routes.register_routes import register_all_routes
from app.utils.logger import logger

# ------------------------------------------------------------
# Initialize FastAPI application
# ------------------------------------------------------------
app = FastAPI(
    title="ChatGPT Team Relay",
    version="2.61.0",
    description="An OpenAI-compatible API relay implementing /v1/* routes, tools, and plugin endpoints.",
)

# ------------------------------------------------------------
# CORS setup (safe origins for plugin and SDK)
# ------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://chat.openai.com",
        "https://platform.openai.com",
        "https://chatgpt-team-relay.onrender.com",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------
# Middleware stack
# ------------------------------------------------------------
# 1. Schema validation — validates /v1/responses payloads
app.add_middleware(SchemaValidationMiddleware)
# 2. P4 orchestrator — forwards and logs all /v1 requests
app.add_middleware(P4OrchestratorMiddleware)

# ------------------------------------------------------------
# Register all /v1 routes
# ------------------------------------------------------------
register_all_routes(app)

# ------------------------------------------------------------
# Health and metadata endpoints
# ------------------------------------------------------------
@app.get("/health", tags=["system"])
async def health_check():
    """Basic health endpoint for Render monitoring."""
    return {
        "status": "ok",
        "service": "chatgpt-team-relay",
        "sdk_version": "2.61.0",
        "versioned": False,
    }


@app.get("/v1/health", tags=["system"])
async def health_check_v1():
    """Versioned health endpoint used by SDKs."""
    return {
        "status": "ok",
        "service": "chatgpt-team-relay",
        "sdk_version": "2.61.0",
        "versioned": True,
    }


@app.get("/", tags=["system"])
async def root():
    """Root discovery endpoint with environment info."""
    return {
        "object": "relay",
        "status": "online",
        "sdk_python": "2.61.0",
        "sdk_node": "6.7.0",
        "base_url": os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1"),
    }


# ------------------------------------------------------------
# OpenAPI schema route for plugin discovery
# ------------------------------------------------------------
@app.get("/schemas/openapi.yaml", include_in_schema=False)
async def get_openapi_schema():
    """Serve OpenAPI 3.1 schema for ChatGPT plugin and SDK discovery."""
    schema_path = os.path.join(os.path.dirname(__file__), "..", "schemas", "openapi.yaml")
    if not os.path.exists(schema_path):
        return JSONResponse({"error": "OpenAPI schema not found"}, status_code=404)
    return FileResponse(schema_path, media_type="application/yaml")


# ------------------------------------------------------------
# Startup and shutdown lifecycle events
# ------------------------------------------------------------
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Starting ChatGPT Team Relay...")
    base_url = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    logger.info(f"🌐 Upstream base URL: {base_url}")
    logger.info("✅ Middleware stack: SchemaValidation → P4Orchestrator")
    logger.info("✅ Routes: /v1/* registered and ready.")
    logger.info("📘 OpenAPI schema available at /schemas/openapi.yaml")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🛑 Relay shutting down gracefully.")


# ------------------------------------------------------------
# Local development entrypoint
# ------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=int(os.getenv("PORT", 10000)),
        reload=True,
    )
