"""
p4_orchestrator.py — Primary Orchestration Middleware
────────────────────────────────────────────────────────────
Intercepts all HTTP traffic and routes API-bound requests
to the proper relay handler.

Aligned with:
  • openai-python SDK v2.61
  • openai-node SDK v6.7.0
  • OpenAI API Reference (2025-10)

Responsibilities:
  • Delegate /v1/* endpoints to forward_openai.py
  • Handle both streaming and non-streaming requests
  • Provide consistent error schema
  • Log request lifecycles and latencies
"""

import os
import json
import time
import httpx
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from app.api.forward_openai import forward_to_openai
from app.utils.logger import log


class P4OrchestratorMiddleware(BaseHTTPMiddleware):
    """Middleware orchestrator for OpenAI-compatible relay traffic."""

    def __init__(self, app):
        super().__init__(app)
        self.timeout = float(os.getenv("RELAY_TIMEOUT", 120))

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        method = request.method.upper()
        start = time.perf_counter()

        # Local endpoints bypass orchestration
        if not path.startswith("/v1"):
            return await call_next(request)

        # Log intercepted request
        log.info(json.dumps({
            "event": "orchestrate_request",
            "method": method,
            "path": path,
            "client": request.client.host if request.client else None
        }))

        try:
            # Delegate directly to OpenAI forwarder for streaming safety
            response = await forward_to_openai(request, path)

            elapsed = round((time.perf_counter() - start) * 1000, 2)
            log.info(json.dumps({
                "event": "orchestrate_complete",
                "path": path,
                "status": getattr(response, "status_code", None),
                "elapsed_ms": elapsed
            }))

            return response

        except httpx.RequestError as e:
            log.error(f"[P4] Network error: {e}")
            return JSONResponse(
                {
                    "error": {
                        "message": str(e),
                        "type": "network_error",
                        "code": "request_failed",
                    }
                },
                status_code=502,
            )

        except Exception as e:
            log.exception(f"[P4] Internal relay error: {e}")
            return JSONResponse(
                {
                    "error": {
                        "message": f"Relay internal error: {str(e)}",
                        "type": "internal_error",
                        "code": "relay_failure",
                    }
                },
                status_code=500,
            )
