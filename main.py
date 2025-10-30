# ==========================================================
# main.py — ChatGPT Team Relay (Ground Truth Edition)
# ==========================================================
"""
Main FastAPI entrypoint for ChatGPT Team Relay.
Implements a complete OpenAI-compatible API surface:
  • /v1/responses  (stream + non-stream)
  • /v1/files       (multipart upload)
  • /v1/responses/tools and /v1/tools
  • /v1/conversations
  • /v1/realtime
and other /v1 routes.
"""

import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.routes.register_routes import register_routes
from app.middleware.validation import ResponseValidationMiddleware
from app.middleware.p4_orchestrator import P4OrchestratorMiddleware


# ==========================================================
# Environment setup
# ==========================================================
load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE = os.getenv("OPENAI_BASE_URL", "https://api.openai.com")
CHAIN_WAIT_MODE = os.getenv("CHAIN_WAIT_MODE", "false").lower() == "true"
ENABLE_STREAM = os.getenv("ENABLE_STREAM", "false").lower() == "true"
PORT = int(os.getenv("PORT", 8080))

# ==========================================================
# Logging
# ==========================================================
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
)
logger = logging.getLogger("chatgpt-team-relay")

logger.info("🚀 Launching ChatGPT Team Relay — Ground Truth Edition")
logger.info(f"OpenAI Base: {OPENAI_BASE}")
logger.info(f"CHAIN_WAIT_MODE={CHAIN_WAIT_MODE}, ENABLE_STREAM={ENABLE_STREAM}")
if not API_KEY:
    logger.warning("⚠️  No OPENAI_API_KEY found — upstream endpoints may fail.")


# ==========================================================
# FastAPI app
# ==========================================================
app = FastAPI(
    title="ChatGPT Team Relay API",
    description="OpenAI-compatible relay for Responses, Tools, Files, Vector Stores, and Realtime.",
    version="2025.10",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ----------------------------------------------------------
# Middleware
# ----------------------------------------------------------
allowed_origins = os.getenv("CORS_ALLOW_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(ResponseValidationMiddleware)
app.add_middleware(P4OrchestratorMiddleware)

# ----------------------------------------------------------
# Route registration
# ----------------------------------------------------------
register_routes(app)
logger.info("✅ All /v1 routes registered successfully.")


# ==========================================================
# Meta & health routes
# ==========================================================
@app.get("/", tags=["Meta"])
async def root():
    return {
        "service": "ChatGPT Team Relay",
        "status": "running",
        "version": "Ground Truth Edition v2025.10",
        "chain_wait_mode": CHAIN_WAIT_MODE,
        "enable_stream": ENABLE_STREAM,
        "openai_base": OPENAI_BASE,
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "version": "2025.10"}


# ==========================================================
# Entry point
# ==========================================================
if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    logger.info(f"🌐 Running on http://{host}:{PORT}")
    uvicorn.run(
        "main:app",
        host=host,
        port=PORT,
        reload=True,
        log_level="info",
    )
