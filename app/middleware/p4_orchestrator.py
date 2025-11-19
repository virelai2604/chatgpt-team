"""
p4_orchestrator.py — Request Orchestration Middleware
──────────────────────────────────────────────────────
Decides whether a request should be handled locally by FastAPI
routes or forwarded upstream to the OpenAI API via forward_openai_request.
"""

import logging
from typing import Callable, Awaitable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.api.forward_openai import forward_openai_request

logger = logging.getLogger("relay.orchestrator")


class P4OrchestratorMiddleware(BaseHTTPMiddleware):
    """
    Orchestration rules:

      • Non-/v1 paths → always handled locally by FastAPI.
      • /v1/health and /schemas/openapi.yaml → local meta endpoints.
      • /v1/tools and /v1/tools/{tool_id} → local hosted tools registry.
      • Known local routers mounted in main.py handle specific /v1/* paths.
      • Everything else under /v1/* → forwarded upstream to OPENAI_API_BASE.

    This keeps the relay OpenAI-compatible while allowing local value-add
    surfaces (tools, health, actions) to coexist cleanly.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        path = request.url.path

        # Non-API paths: let FastAPI handle them as-is.
        if not path.startswith("/v1/") and not path.startswith("/schemas/"):
            logger.debug("Non-API path %s → local FastAPI route", path)
            return await call_next(request)

        # Local meta endpoints
        if path == "/v1/health" or path == "/schemas/openapi.yaml":
            logger.debug("Local meta path %s → local FastAPI route", path)
            return await call_next(request)

        # Local tools registry (for ChatGPT Actions)
        if path.startswith("/v1/tools"):
            logger.debug("Tools path %s → local tools router", path)
            return await call_next(request)

        # Known local routers (responses, conversations, files, etc.) are
        # already registered in main.py, so we allow FastAPI to resolve them.
        # Any /v1/* route that is not defined locally will fall through to
        # the forwarder below.
        known_local_prefixes = (
            "/v1/responses",
            "/v1/conversations",
            "/v1/files",
            "/v1/vector_stores",
            "/v1/embeddings",
            "/v1/realtime",
            "/v1/models",
            "/v1/images",
            "/v1/videos",
            "/v1/actions",
        )
        for prefix in known_local_prefixes:
            if path.startswith(prefix):
                logger.debug("Known local API path %s → FastAPI router", path)
                return await call_next(request)

        # Fallback: forward all other /v1/* requests upstream to OpenAI.
        logger.debug("Fallback OpenAI path %s → forward_openai_request", path)
        return await forward_openai_request(request)