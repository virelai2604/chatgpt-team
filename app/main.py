# ================================================================
# main.py — ChatGPT Team Relay (OpenAI-Compatible)
# ================================================================
# Entry point for the ChatGPT Team Relay running on Render.com
# Version: 2.0  |  API Parity: openai-python 2.6.1 / openai-node 6.7.0
# ================================================================

import os
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from app.routes import register_routes
from app.api.passthrough_proxy import router as passthrough_router
from app.api.forward_openai import forward_to_openai
from app.utils.logger import setup_logger

# ================================================================
# Logging Configuration
# ================================================================
setup_logger()
logger = logging.getLogger("relay")

# ================================================================
# FastAPI App Initialization
# ================================================================
app = FastAPI(
    title="ChatGPT Team Relay API",
    version="2.0",
    description=(
        "OpenAI-compatible relay API with ground-truth validation.\n"
        "Implements SDK v2.6.1 (Python) and v6.7.0 (Node) endpoints.\n"
        "Supports Responses, Realtime, Files, Vector Stores, Tools, and Conversations."
    ),
)

# ================================================================
# Static File Mounts for Plugin + Schema Discovery
# ================================================================
static_dir = os.path.join(os.path.dirname(__file__), "static")
schemas_dir = os.path.join(os.path.dirname(__file__), "schemas")

# Public .well-known folder for ChatGPT Actions
well_known_path = os.path.join(static_dir, ".well-known")
if os.path.exists(well_known_path):
    app.mount("/.well-known", StaticFiles(directory=well_known_path), name="well-known")
    logger.info("📘 Mounted /.well-known for plugin manifest")

# OpenAPI schema served directly for ChatGPT Actions
if os.path.exists(schemas_dir):
    app.mount("/schemas", StaticFiles(directory=schemas_dir), name="schemas")
    logger.info("📘 Mounted /schemas for OpenAPI schema access")

# ================================================================
# CORS Configuration (Required for ChatGPT Actions)
# ================================================================
allowed_origins = os.getenv(
    "CORS_ALLOW_ORIGINS",
    "https://chat.openai.com,https://platform.openai.com"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in allowed_origins],
    allow_credentials=True,
    allow_methods=os.getenv(
        "CORS_ALLOW_METHODS", "GET,POST,PUT,PATCH,DELETE,OPTIONS"
    ).split(","),
    allow_headers=os.getenv("CORS_ALLOW_HEADERS", "*").split(","),
)

# ================================================================
# Register All Routes
# ================================================================
register_routes(app)

# ================================================================
# Universal Passthrough for Future /v1/* Endpoints
# ================================================================
@app.api_route("/v1/{endpoint:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def universal_passthrough(request: Request, endpoint: str):
    """
    Automatically forwards any unknown /v1/* endpoint to OpenAI.
    Example: /v1/assistants, /v1/fine_tuning/jobs, /v1/batches
    Future-proofs the relay as the OpenAI API evolves.
    """
    upstream_path = f"/v1/{endpoint}"
    logger.info(f"🔄 Universal passthrough triggered for {upstream_path}")

    resp = await forward_to_openai(request, upstream_path)
    content_type = resp.headers.get("content-type", "")

    # Handle streaming responses (SSE)
    if "text/event-stream" in content_type:
        async def stream_generator():
            async for chunk in resp.aiter_bytes():
                yield chunk
        return StreamingResponse(stream_generator(), media_type="text/event-stream")

    # Handle JSON or plain text
    try:
        return JSONResponse(resp.json(), status_code=resp.status_code)
    except Exception:
        return JSONResponse(
            {
                "object": "proxy_response",
                "path": upstream_path,
                "status": resp.status_code,
                "content_type": content_type,
                "body": resp.text[:2000],
            },
            status_code=resp.status_code,
        )

# ================================================================
# Fallback Proxy for Truly Unrecognized Routes
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
# Startup Message
# ================================================================
@app.on_event("startup")
async def on_startup():
    logger.info("🚀 ChatGPT Team Relay startup complete.")
    logger.info("   - OpenAI passthrough active")
    logger.info("   - Universal passthrough enabled for /v1/*")
    logger.info("   - Routes and tools registered successfully")
    logger.info("   - Ready for ChatGPT Actions integration")
