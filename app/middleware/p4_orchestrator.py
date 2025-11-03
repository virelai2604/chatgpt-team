"""
P4 Orchestrator Middleware — Export-based OpenAI Proxy (Final Version)
────────────────────────────────────────────────────────────
Implements OpenAI-compatible request orchestration, fully aligned with API Reference (truth source).
Automatically bypasses local routes like /health, /docs, and /openapi.json.
"""

import os
import httpx
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from app.utils.logger import log


class P4OrchestratorMiddleware(BaseHTTPMiddleware):
    """
    Core orchestration layer for ChatGPT-Team Relay.
    Handles forwarding of /v1/* API requests to OpenAI or another compatible backend.
    """

    def __init__(self, app):
        super().__init__(app)
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "missing_key")
        self.OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
        self.TIMEOUT = int(os.getenv("RELAY_TIMEOUT", "120"))

    # ---------------------------------------------------------------------------
    # Main entrypoint for all incoming HTTP requests
    # ---------------------------------------------------------------------------

    async def dispatch(self, request: Request, call_next):
        """
        Intercepts incoming requests.
        Forwards only /v1/* requests to upstream OpenAI API.
        Allows local routes (/health, /docs, /openapi.json, etc.) to pass through.
        """

        path = request.url.path
        method = request.method

        # -----------------------------------------------------------------------
        # Bypass local FastAPI endpoints — do NOT forward upstream
        # -----------------------------------------------------------------------
        if not path.startswith("/v1"):
            return await call_next(request)

        log.info(f"[P4] Handling {method} {path}")

        try:
            # Parse payload for mutating requests
            payload = None
            if method in ("POST", "PATCH"):
                payload = await request.json()

            # Forward /v1 requests to OpenAI-compatible upstream
            response = await self._forward_to_upstream(request, payload)
            return response

        except httpx.RequestError as e:
            log.error(f"[P4] Network error forwarding request: {e}")
            return JSONResponse({"error": str(e)}, status_code=502)

        except Exception as e:
            log.exception(f"[P4] Internal error: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)

    # ---------------------------------------------------------------------------
    # Upstream forwarder — sends request to OpenAI API
    # ---------------------------------------------------------------------------

    async def _forward_to_upstream(self, request: Request, payload: dict | None):
        """
        Sends /v1/* requests to the configured OpenAI API base.
        Returns the upstream response as JSONResponse.
        """

        # Normalize endpoint for OpenAI API (strip local /v1 prefix)
        endpoint = request.url.path.replace("/v1", "")
        target_url = f"{self.OPENAI_API_BASE}{endpoint}"

        headers = {
            "Authorization": f"Bearer {self.OPENAI_API_KEY}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
            if request.method == "POST":
                upstream = await client.post(target_url, json=payload, headers=headers)
            elif request.method == "GET":
                upstream = await client.get(target_url, headers=headers)
            elif request.method == "PATCH":
                upstream = await client.patch(target_url, json=payload, headers=headers)
            elif request.method == "DELETE":
                upstream = await client.delete(target_url, headers=headers)
            else:
                return JSONResponse(
                    {"error": f"Unsupported method {request.method}"},
                    status_code=405,
                )

        # Convert upstream response to JSON
        try:
            data = upstream.json()
        except Exception:
            data = {"error": "Invalid JSON from upstream", "raw": upstream.text}

        log.info(f"[P4] Upstream {request.method} {endpoint} → {upstream.status_code}")
        return JSONResponse(data, status_code=upstream.status_code)
