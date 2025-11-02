# ================================================================
# main.py — ChatGPT Team Relay (Ground Truth API v1.7)
# ================================================================
# A production-grade FastAPI relay that mirrors OpenAI’s API behavior.
# Features:
#   • /v1/* passthrough for all official endpoints
#   • Local health + root routes (for Render + Uptime)
#   • Ground truth request validation + middleware orchestration
#   • SDK-aligned JSON error schemas and streaming
# ================================================================

import os
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

# --- App internal imports ---
from app.routes.register_routes import register_routes
from app.api.passthrough_proxy import router as passthrough_router
from app.api.forward_openai import forward_to_openai
from app.middleware.p4_orchestrator import P4OrchestratorMiddleware
from app.middleware.validation import validate_request
from app.utils.logger import setup_logger

# ================================================================
# Logging Setup
# ================================================================
setup_logger()
logger = logging.getLogger("relay")

# ================================================================
# FastAPI Application Setup
# ================================================================
app = FastAPI(
    title="ChatGPT Team Relay API",
    version="1.7",
    description="OpenAI-compatible proxy API — Ground Truth aligned for SDK 2.6.1",
)

# ================================================================
# Static File Mounts (for ChatGPT Actions / Plugin Manifest)
# ================================================================
static_dir = os.path.join(os.path.dirname(__file__), "static")
schemas_dir = os.path.join(os.path.dirname(__file__), "schemas")

well_known_path = os.path.join(static_dir, ".well-known")
if os.path.exists(well_known_path):
    app.mount("/.well-known", StaticFiles(directory=well_known_path), name="well-known")
    logger.info("📘 Mounted /.well-known for plugin manifest")

if os.path.exists(schemas_dir):
    app.mount("/schemas", StaticFiles(directory=schemas_dir), name="schemas")
    logger.info("📘 Mounted /schemas for OpenAPI schema access")

# ================================================================
# CORS Configuration
# ================================================================
allowed_origins = os.getenv(
    "CORS_ALLOW_ORIGINS",
    "https://chat.openai.com,https://platform.openai.com"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in allowed_origins],
    allow_credentials=True,
    allow_methods=os.getenv(
        "CORS_ALLOW_METHODS", "GET,POST,PUT,PATCH,DELETE,OPTIONS"
    ).split(","),
    allow_headers=os.getenv("CORS_ALLOW_HEADERS", "*").split(","),
)

# ================================================================
# Middleware Integration
# ================================================================
app.add_middleware(P4OrchestratorMiddleware)

@app.middleware("http")
async def schema_validation_middleware(request: Request, call_next):
    validation_response = await validate_request(request)
    if validation_response:
        return validation_response
    return await call_next(request)

# ================================================================
# Root and Health Routes (must be declared BEFORE passthrough)
# ================================================================
@app.get("/", tags=["meta"])
async def root():
    """Root endpoint for Render + uptime monitoring."""
    return {
        "object": "relay",
        "status": "ok",
        "message": "ChatGPT Team Relay active and healthy",
        "docs": "https://platform.openai.com/docs/api-reference"
    }

@app.get("/health", tags=["meta"])
async def health():
    """Simple health check endpoint."""
    return {"status": "ok", "uptime": "good"}

# ================================================================
# Register Core OpenAI-Compatible Route Modules
# ================================================================
register_routes(app)

# ================================================================
# Universal Passthrough for /v1/* Endpoints
# ================================================================
@app.api_route("/v1/{endpoint:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def universal_passthrough(request: Request, endpoint: str):
    """Forward any unrecognized /v1/* endpoint to OpenAI upstream."""
    logger.info(f"🔄 Universal passthrough triggered for /v1/{endpoint}")
    upstream_path = f"/v1/{endpoint}"

    resp = await forward_to_openai(request, upstream_path)

    content_type = getattr(resp, "headers", {}).get("content-type", "")
    if "text/event-stream" in content_type:
        async def stream():
            async for chunk in resp.aiter_bytes():
                yield chunk
        return StreamingResponse(stream(), media_type="text/event-stream")

    if hasattr(resp, "json"):
        try:
            return JSONResponse(resp.json(), status_code=resp.status_code)
        except Exception:
            pass

    return JSONResponse(
        {
            "object": "proxy_response",
            "path": upstream_path,
            "status": getattr(resp, "status_code", 500),
            "content_type": content_type,
            "body": getattr(resp, "text", "")[:2000],
        },
        status_code=getattr(resp, "status_code", 500),
    )

# ================================================================
# Additional Passthrough Router for non-/v1 paths
# ================================================================
app.include_router(passthrough_router)

# ================================================================
# Exception Handling
# ================================================================
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        {"object": "error", "message": str(exc), "path": str(request.url)},
        status_code=500,
    )

# ================================================================
# Startup Logging
# ================================================================
@app.on_event("startup")
async def on_startup():
    logger.info("🚀 ChatGPT Team Relay startup complete.")
    logger.info("   - OpenAI passthrough active")
    logger.info("   - Universal /v1 passthrough enabled")
    logger.info("   - Schema validation middleware active")
    logger.info("   - Routes and tools registered successfully")
    logger.info("   - Ready for ChatGPT Actions integration")
