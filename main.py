# ==========================================================
# main.py — ChatGPT Team Relay (Ground Truth Edition)
# ==========================================================
"""
Main FastAPI entrypoint for the ChatGPT Team Relay.
Implements the Ground Truth Edition v2025.10 — a fully
OpenAI-compatible API mirror with streaming and CHAIN_WAIT support.
"""

import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from app.routes.register_routes import register_routes

# ==========================================================
# Environment Loader
# ==========================================================
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
chain_wait_mode = os.getenv("CHAIN_WAIT_MODE", "false").lower() == "true"

# ==========================================================
# Startup Info
# ==========================================================
if not api_key:
    print("[WARN] OPENAI_API_KEY not found in environment.")
else:
    print(f"[OK] Loaded OPENAI_API_KEY: {api_key[:8]}... (hidden)")

if chain_wait_mode:
    print("[INFO] Relay is running in CHAIN_WAIT_MODE=True — waiting for object completion.")
else:
    print("[INFO] Relay is running in normal (non-wait) mode.")

# ==========================================================
# Logging Configuration
# ==========================================================
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)

# ==========================================================
# App Initialization
# ==========================================================
app = FastAPI(
    title="ChatGPT Team Relay API",
    description="Ground Truth compliant OpenAI-compatible relay (v2025.10)",
    version="2025.10",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ==========================================================
# CORS Middleware
# ==========================================================
allowed_origins = os.getenv("CORS_ALLOW_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================================
# Route Registration
# ==========================================================
register_routes(app)

# ==========================================================
# Root + Health
# ==========================================================
@app.get("/", tags=["Meta"])
async def root():
    return {
        "service": "ChatGPT Team Relay (Cloudflare / Render)",
        "status": "running",
        "version": "Ground Truth Edition v2025.10",
        "docs": "/docs",
        "openapi_spec": "/v1/openapi.yaml",
        "health": "/health",
        "upstream": os.getenv("OPENAI_BASE_URL", "https://api.openai.com"),
        "chain_wait_mode": chain_wait_mode,
    }

@app.get("/health", tags=["Health"])
async def healthcheck():
    return {"status": "ok", "version": "2025.10"}

# ==========================================================
# Local Run Entrypoint
# ==========================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8080)),
        reload=True
    )
