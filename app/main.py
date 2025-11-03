"""
main.py — FastAPI Entry Point for ChatGPT Team Relay
────────────────────────────────────────────────────────────
Fully OpenAI-compatible relay server aligned with:
  • openai-python SDK v2.61
  • openai-node SDK v6.7.0
  • OpenAI API Reference (2025-10)

Features:
  • Middleware orchestration (P4 + schema validation)
  • Route auto-registration (/v1/*)
  • Structured logging
  • Health endpoints
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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
    description="A fully OpenAI-compatible API relay implementing /v1/* routes, tools, and plugin endpoints.",
)

# ------------------------------------------------------------
# CORS setup (for plugin + SDK browser calls)
# ------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------
# Middleware stack
# ------------------------------------------------------------
# 1. Schema validation (JSON schema check for /v1/responses)
app.add_middleware(SchemaValidationMiddleware)
# 2. P4 orchestrator (handles OpenAI request forwarding)
app.add_middleware(P4OrchestratorMiddleware)

# ------------------------------------------------------------
# Register all /v1 routes
# ------------------------------------------------------------
register_all_routes(app)

# ------------------------------------------------------------
# Health and root endpoints
# ------------------------------------------------------------
@app.get("/health")
async def health_check():
    """Simple local service health endpoint — not proxied to OpenAI."""
    return {
        "status": "ok",
        "service": "chatgpt-team-relay",
        "sdk_version": "2.61.0",
        "versioned": False,
    }


@app.get("/v1/health")
async def health_check_v1():
    """Versioned health endpoint (used by SDK tests)."""
    return {
        "status": "ok",
        "service": "chatgpt-team-relay",
        "sdk_version": "2.61.0",
        "versioned": True,
    }


@app.get("/")
async def root():
    """Root endpoint for discovery."""
    return {
        "object": "relay",
        "status": "online",
        "sdk_python": "2.61.0",
        "sdk_node": "6.7.0",
        "base_url": os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1"),
    }

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


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🛑 Relay shutting down gracefully.")


# ------------------------------------------------------------
# Local development entry
# ------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=int(os.getenv("PORT", 10000)),
        reload=True,
    )
