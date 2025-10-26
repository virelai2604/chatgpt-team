# ==========================================================
#  app/api/passthrough_proxy.py — BIFL v2.3.3+
# ==========================================================
#  Smart passthrough router for OpenAI-compatible /v1/* APIs.
#  Integrates with forward_openai() for full streaming support.
# ==========================================================

import os
import uuid
import logging
import asyncio
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from app.api.forward import forward_openai
from app.utils.error_handler import error_response

# ──────────────────────────────────────────────
#  Configuration
# ──────────────────────────────────────────────
DEBUG_MODE = os.getenv("DEBUG", "false").lower() == "true"
RELAY_TIMEOUT = int(os.getenv("RELAY_TIMEOUT", "120"))
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com")

router = APIRouter()
logger = logging.getLogger("bifl.passthrough")

logging.basicConfig(
    level=logging.DEBUG if DEBUG_MODE else logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
)

# ──────────────────────────────────────────────
#  Internal utilities
# ──────────────────────────────────────────────
def _trace() -> str:
    """Generate a UUID trace ID for each proxied request."""
    return str(uuid.uuid4())


def _should_block(path: str) -> bool:
    """Block deprecated or unsafe legacy endpoints."""
    blocked = [
        "/v1/completions",
        "/v1/chat/completions",
        "/v1/engines",
        "/v1/answers",
    ]
    return any(path.startswith(b) for b in blocked)


# ──────────────────────────────────────────────
#  Main passthrough endpoint
# ──────────────────────────────────────────────
@router.api_route("/v1/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def passthrough_v1(request: Request, path: str):
    """
    Relay any OpenAI-style /v1/* endpoint through the BIFL forwarder.
    Adds trace logging, safety checks, and unified error handling.
    """
    trace_id = _trace()
    endpoint = f"/v1/{path}"

    if _should_block(endpoint):
        logger.warning(f"[TRACE {trace_id}] Blocked deprecated endpoint: {endpoint}")
        return error_response(
            "deprecated_endpoint",
            f"The endpoint '{endpoint}' is deprecated or not supported.",
            403,
            {"trace_id": trace_id},
        )

    # Normalize video aliases → responses
    if endpoint.startswith("/v1/videos"):
        endpoint = "/v1/responses"

    try:
        if DEBUG_MODE:
            logger.debug(f"[TRACE {trace_id}] Forwarding → {endpoint}")

        response = await forward_openai(request, endpoint)

        # Forward returns either JSONResponse or StreamingResponse
        if response:
            response.headers["X-BIFL-Trace"] = trace_id
            response.headers["X-BIFL-Version"] = "2.3.3"
        return response

    except asyncio.TimeoutError:
        logger.error(f"[TRACE {trace_id}] Timeout after {RELAY_TIMEOUT}s at {endpoint}")
        return error_response(
            "timeout",
            f"Request timed out after {RELAY_TIMEOUT} seconds.",
            504,
            {"trace_id": trace_id},
        )

    except Exception as e:
        logger.exception(f"[TRACE {trace_id}] Passthrough error at {endpoint}: {e}")
        return error_response(
            "relay_exception",
            str(e),
            502,
            {"trace_id": trace_id},
        )


# ──────────────────────────────────────────────
#  Health / Debug Endpoint
# ──────────────────────────────────────────────
@router.get("/relay/health")
async def relay_health():
    """Lightweight relay status endpoint."""
    return JSONResponse(
        content={
            "status": "ok",
            "bifl_version": "2.3.3",
            "base_url": OPENAI_BASE_URL,
        },
        status_code=200,
    )
