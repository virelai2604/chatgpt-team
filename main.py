# ==========================================================
# main.py — ChatGPT Team Relay (Ground Truth Edition)
# ==========================================================
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Core modules
from app.routes.responses import router as responses_router
from app.routes.realtime import router as realtime_router
from app.routes.files import router as files_router
from app.routes.vector_stores import router as vector_stores_router
from app.routes.models import router as models_router
from app.routes.passthrough_proxy import router as passthrough_router
from app.utils.error_handler import register_error_handlers

# ==========================================================
# App initialization
# ==========================================================
logging.basicConfig(level=logging.INFO)
app = FastAPI(
    title="ChatGPT Team Relay API",
    description="Ground Truth compliant OpenAI-compatible relay (2025.10).",
    version="2025.10",
)

# CORS matches OpenAI SDK’s permissive default
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================================
# Route registration
# ==========================================================
app.include_router(models_router)
app.include_router(files_router)
app.include_router(vector_stores_router)
app.include_router(responses_router)
app.include_router(realtime_router)
app.include_router(passthrough_router)

# ==========================================================
# Error handling
# ==========================================================
app = register_error_handlers(app)

# ==========================================================
# Root route for health
# ==========================================================
@app.get("/")
async def healthcheck():
    return {"status": "ok", "version": "2025.10"}
