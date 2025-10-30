# ==========================================================
# main.py — ChatGPT Team Relay (Ground Truth Edition)
# ==========================================================
"""
Main FastAPI entrypoint for the ChatGPT Team Relay.
Implements the Ground Truth Edition v2025.10 — fully OpenAI-compatible API mirror.
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
if not api_key:
    print("[WARN] OPENAI_API_KEY not found in environment.")
else:
    print(f"[OK] Loaded OPENAI_API_KEY: {api_key[:8]}... (hidden)")

# ==========================================================
# App Initialization
# ==========================================================
logging.basicConfig(level=logging.INFO)
app = FastAPI(
    title="ChatGPT Team Relay API",
    description="Ground Truth compliant OpenAI-compatible relay (v2025.10).",
    version="2025.10",
)

# ==========================================================
# CORS
# ==========================================================
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
    }

@app.get("/health", tags=["Health"])
async def healthcheck():
    return {"status": "ok", "version": "2025.10"}

# ==========================================================
# Local Run
# ==========================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8080)),
        reload=True
    )
