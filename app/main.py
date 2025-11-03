import os
from fastapi import FastAPI
from app.middleware.p4_orchestrator import P4OrchestratorMiddleware
from app.routes.register_routes import register_routes
from app.utils.logger import setup_logger

# Initialize logger and FastAPI app
log = setup_logger()
app = FastAPI(title="OpenAI Relay Server", version="2.6.1")

# Apply orchestrator middleware
app.add_middleware(P4OrchestratorMiddleware)

# ---------------------------------------------------------
# ✅ Local health checks (ground-truth aligned with SDK 2.6.1)
# ---------------------------------------------------------
@app.get("/health")
async def health_check():
    """Simple local service health endpoint — not proxied to OpenAI."""
    return {
        "status": "ok",
        "service": "openai-relay",
        "sdk_version": "2.6.1",
        "versioned": False
    }


@app.get("/v1/health")
async def health_check_v1():
    """Optional versioned health route for test suite parity."""
    return {
        "status": "ok",
        "service": "openai-relay",
        "sdk_version": "2.6.1",
        "versioned": True
    }

# ---------------------------------------------------------
# ✅ Register OpenAI-compatible /v1 routes
# ---------------------------------------------------------
register_routes(app)

# ---------------------------------------------------------
# ✅ Startup logging
# ---------------------------------------------------------
@app.on_event("startup")
async def startup_event():
    log.info("🚀 Application startup — initializing relay components.")
    log.info("✅ P4 Orchestrator Middleware loaded and ready.")
    base_url = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    log.info(f"🌐 Relay base URL: {base_url}")


@app.on_event("shutdown")
async def shutdown_event():
    log.info("🛑 Relay shutting down gracefully.")


# ---------------------------------------------------------
# ✅ Run locally with `uvicorn app.main:app --port 10000`
# ---------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=int(os.getenv("PORT", 10000)), reload=True)
