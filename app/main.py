"""
main.py — ChatGPT Team Relay Entry Point
────────────────────────────────────────
This is the unified app bootstrap for your OpenAI-compatible relay.

Features:
  • Registers all /v1 endpoints (responses, files, models, etc.)
  • Integrates validation + orchestration middleware
  • Loads /v1/tools manifest dynamically
  • Serves /schemas/openapi.yaml for ChatGPT Actions / Plugins
  • Handles startup + graceful shutdown
"""

import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, JSONResponse

# Core imports
from app.middleware.validation import SchemaValidationMiddleware
from app.middleware.p4_orchestrator import P4OrchestratorMiddleware
from app.utils.logger import relay_log as logger
from app.utils.error_handler import register_error_handlers
from app.routes.register_routes import register_all_routes


# ============================================================
# 1. FastAPI App Initialization
# ============================================================

def create_app() -> FastAPI:
    app = FastAPI(
        title="ChatGPT Team Relay",
        version="2025.11",
        description="OpenAI-compatible API relay with full SDK parity.",
        contact={"name": "ChatGPT Team", "url": "https://platform.openai.com"}
    )

    # ------------------------------------------------------------
    # Middleware stack
    # ------------------------------------------------------------
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(SchemaValidationMiddleware)
    app.add_middleware(P4OrchestratorMiddleware)

    # ------------------------------------------------------------
    # Global error handling
    # ------------------------------------------------------------
    register_error_handlers(app)

    # ------------------------------------------------------------
    # Route registration
    # ------------------------------------------------------------
    register_all_routes(app)

    # ------------------------------------------------------------
    # Local schema serving
    # ------------------------------------------------------------
    @app.get("/schemas/openapi.yaml", tags=["schemas"])
    async def get_openapi_schema():
        """Serve OpenAPI spec (YAML) for ChatGPT Actions."""
        schema_path = os.path.join(os.getcwd(), "schemas", "openapi.yaml")
        if not os.path.exists(schema_path):
            return JSONResponse({"error": "Schema not found."}, status_code=404)
        with open(schema_path, "r", encoding="utf-8") as f:
            content = f.read()
        return PlainTextResponse(content, media_type="text/yaml", status_code=200)

    # ------------------------------------------------------------
    # Root route
    # ------------------------------------------------------------
    @app.get("/", tags=["system"])
    async def root():
        return {
            "object": "relay_root",
            "service": "ChatGPT Team Relay",
            "status": "ok",
            "version": app.version,
        }

    return app


# ============================================================
# 2. App Factory & Entrypoint
# ============================================================

app = create_app()


@app.on_event("startup")
async def startup_event():
    """Lifecycle startup event."""
    logger.info("🚀 ChatGPT Team Relay starting up...")
    os.environ.setdefault("OPENAI_API_BASE", "https://api.openai.com/v1")
    if not os.getenv("OPENAI_API_KEY"):
        logger.warning("⚠️  OPENAI_API_KEY is not set. Requests will fail upstream.")
    logger.info("✅ Environment variables initialized.")


@app.on_event("shutdown")
async def shutdown_event():
    """Lifecycle shutdown event."""
    logger.info("🛑 ChatGPT Team Relay shutting down...")


# ============================================================
# 3. Dev Server Entry
# ============================================================

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=bool(os.getenv("RELAY_DEBUG", "true") == "true"),
        log_level="info",
    )
