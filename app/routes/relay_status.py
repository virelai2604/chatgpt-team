# ==========================================================
# app/routes/relay_status.py — Relay Health Check
# ==========================================================
from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(tags=["Relay"])

@router.get("/health")
async def health():
    """
    Lightweight readiness probe for Render and tests.
    """
    return JSONResponse({"status": "ok", "service": "ChatGPT Team Relay"})

@router.get("/v1/relay/status")
async def relay_status():
    """
    Detailed relay health endpoint for diagnostics.
    """
    return JSONResponse({
        "status": "operational",
        "relay_version": "v2.3.4-fp",
        "components": ["routes", "middleware", "forward_openai", "proxy"],
    })
