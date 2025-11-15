"""
p4_orchestrator.py — Request Orchestration Middleware
──────────────────────────────────────────────────────
Intercepts all incoming HTTP requests to the relay,
decides whether to forward them to OpenAI's API or
handle them locally (e.g., ChatGPT Actions, tools, schema, etc.).
"""

import json
import httpx
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.utils.logger import relay_log as logger
import os

OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")


class P4OrchestratorMiddleware(BaseHTTPMiddleware):
    """
    Routes requests:
      • Local endpoints → handled by FastAPI (actions, tools, schema, etc.)
      • OpenAI endpoints (/v1/*) → proxied upstream to OpenAI REST API
    """

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # ==========================================================
        # 1. Log all inbound requests
        # ==========================================================
        logger.info({
            "event": "orchestrate_request",
            "method": request.method,
            "path": path,
            "client": request.client.host,
        })

        # ==========================================================
        # 2. Skip forwarding for local-only routes
        # ==========================================================
        local_prefixes = (
            "/actions/",
            "/schemas/",
            "/v1/tools",
            "/v1/health",
            "/health",
        )

        if any(path.startswith(prefix) for prefix in local_prefixes):
            # Handle internally (e.g., ChatGPT Actions)
            return await call_next(request)

        # ==========================================================
        # 3. Proxy /v1/* requests to OpenAI API
        # ==========================================================
        if path.startswith("/v1/"):
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    upstream_url = f"{OPENAI_API_BASE}{path}"
                    headers = {
                        "Authorization": f"Bearer {OPENAI_API_KEY}",
                        "Content-Type": request.headers.get(
                            "content-type", "application/json"
                        ),
                    }

                    # Read body if available
                    body_bytes = await request.body()
                    body = body_bytes if body_bytes else None

                    logger.info(
                        {
                            "method": request.method,
                            "url": upstream_url,
                            "headers": {"authorization": "Bearer ...", "content-type": headers["Content-Type"]},
                        }
                    )

                    # Match request method
                    if request.method == "GET":
                        upstream_response = await client.get(
                            upstream_url, headers=headers
                        )
                    elif request.method == "POST":
                        upstream_response = await client.post(
                            upstream_url, headers=headers, content=body
                        )
                    elif request.method == "DELETE":
                        upstream_response = await client.delete(
                            upstream_url, headers=headers
                        )
                    else:
                        upstream_response = await client.request(
                            request.method, upstream_url, headers=headers, content=body
                        )

                    return Response(
                        content=upstream_response.content,
                        status_code=upstream_response.status_code,
                        headers=dict(upstream_response.headers),
                        media_type=upstream_response.headers.get("content-type"),
                    )

            except httpx.RequestError as e:
                logger.error({"error": "Upstream request failed", "details": str(e)})
                return Response(
                    content=json.dumps({"error": str(e)}),
                    status_code=502,
                    media_type="application/json",
                )

        # ==========================================================
        # 4. If not /v1/* or local — pass through (fallback)
        # ==========================================================
        return await call_next(request)
