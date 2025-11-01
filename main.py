# ==========================================================
# main.py — ChatGPT Team Relay (Ground Truth 2025.11)
# ==========================================================
"""
Entry point for the ChatGPT Team Relay server.
Implements:
  • OpenAI-compatible /v1 REST routes
  • Unified /v1/responses endpoint (models + tools)
  • Full passthrough to OpenAI API
  • Plugin discovery under /.well-known/ai-plugin.json
"""

import os
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from app.utils.logger import logger
from app.middleware.validation import ResponseValidationMiddleware
from app.middleware.p4_orchestrator import P4OrchestratorMiddleware
from app.routes.register_routes import register_routes
from fastapi.responses import JSONResponse

# ----------------------------------------------------------
# Load environment
# ----------------------------------------------------------
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com")

# ----------------------------------------------------------
# Create app
# ----------------------------------------------------------
app = FastAPI(
    title="ChatGPT Team Relay",
    version="2025.11",
    description="OpenAI-compatible relay server with toolchain support",
)

# ----------------------------------------------------------
# Middleware stack
# ----------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(ResponseValidationMiddleware)
app.add_middleware(P4OrchestratorMiddleware)

# ----------------------------------------------------------
# Register routes
# ----------------------------------------------------------
register_routes(app)

# ----------------------------------------------------------
# Serve static plugin manifest
# ----------------------------------------------------------
app.mount(
    "/.well-known",
    StaticFiles(directory="app/static/.well-known"),
    name="well-known"
)

# ----------------------------------------------------------
# Root and health routes
# ----------------------------------------------------------
@app.get("/")
async def root():
    return {
        "relay": "ChatGPT Team Relay",
        "status": "running",
        "openai_base": OPENAI_BASE_URL,
        "version": "2025.11"
    }

@app.get("/health")
async def health():
    return {"status": "ok", "version": "2025.11"}

# ----------------------------------------------------------
# Global error handler
# ----------------------------------------------------------
@app.exception_handler(Exception)
async def handle_exception(request: Request, exc: Exception):
    logger.error(f"Unhandled exception at {request.url.path}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": str(exc), "path": request.url.path},
    )

# ----------------------------------------------------------
# Startup event
# ----------------------------------------------------------
@app.on_event("startup")
async def on_startup():
    logger.info("🚀 Launching ChatGPT Team Relay — Ground Truth Edition")
    logger.info(f"OpenAI Base: {OPENAI_BASE_URL}")
    logger.info("CHAIN_WAIT_MODE=True, ENABLE_STREAM=True")

    logger.info("🔗 Available /v1 routes:")
    for route in app.routes:
        if getattr(route, "path", "").startswith("/v1"):
            logger.info(f"   {route.path} → {route.name}")
    logger.info("✅ Application startup complete.\n")

# ----------------------------------------------------------
# Entrypoint
# ----------------------------------------------------------
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
