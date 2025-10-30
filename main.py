# ==========================================================
# main.py — ChatGPT Team Relay (Ground Truth Edition)
# ==========================================================
"""
Main FastAPI entrypoint for ChatGPT Team Relay.
Implements the full OpenAI-compatible Responses API,
including /responses/tools, streaming, and CHAIN_WAIT_MODE.
"""

import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from app.routes.register_routes import register_routes
from app.middleware.validation import ResponseValidationMiddleware
from app.middleware.p4_orchestrator import P4OrchestratorMiddleware

# Load environment variables
load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE = os.getenv("OPENAI_BASE_URL", "https://api.openai.com")
CHAIN_WAIT_MODE = os.getenv("CHAIN_WAIT_MODE", "false").lower() == "true"

# Configure logging
logging.basicConfig(level=logging.INFO, format="[%(asctime)s] [%(levelname)s] %(message)s")

# Initialize FastAPI app
app = FastAPI(
    title="ChatGPT Team Relay API",
    description="OpenAI-compatible relay with Responses, Tools, Files, and Realtime support",
    version="2025.10",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS setup
allowed_origins = os.getenv("CORS_ALLOW_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add validation middleware (optional schema validation)
app.add_middleware(ResponseValidationMiddleware)
app.add_middleware(P4OrchestratorMiddleware)

# Register all /v1 routes
register_routes(app)

@app.get("/", tags=["Meta"])
async def root():
    """Root metadata endpoint"""
    return {
        "service": "ChatGPT Team Relay",
        "status": "running",
        "version": "Ground Truth Edition v2025.10",
        "chain_wait_mode": CHAIN_WAIT_MODE,
        "openai_base": OPENAI_BASE,
        "docs": "/docs",
        "health": "/health",
    }

@app.get("/health", tags=["Health"])
async def health():
    """Basic health check"""
    return {"status": "ok", "version": "2025.10"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8080)), reload=True)
