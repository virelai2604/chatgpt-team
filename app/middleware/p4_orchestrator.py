import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.forward_openai import forward_openai_request

logger = logging.getLogger("uvicorn")


class P4OrchestratorMiddleware(BaseHTTPMiddleware):
    """
    Middleware that decides whether to forward a request to the upstream
    OpenAI API or handle it locally inside the relay.

    Rules:
      • If the path starts with /v1/ AND is NOT in the excluded set,
        forward to OpenAI via forward_openai_request.
      • Otherwise, let FastAPI handle it with local routes.

    This design mirrors the official OpenAI REST surface used by the
    latest SDKs (openai-python, openai-node). In particular it forwards:
      • /v1/responses (including built-in tools via the Responses API)
      • /v1/models
      • /v1/files and /v1/files/{file_id}/content
      • /v1/embeddings
      • /v1/vector_stores/** (stores, file_batches, files)
      • /v1/realtime/sessions
      • /v1/conversations/**
    and any future /v1/* endpoints, unchanged.
    """

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        method = request.method

        # Local-only or "special" routes that should NOT be proxied upstream.
        # These are handled by FastAPI routers defined in app.routes/*.
        excluded = (
            path.startswith("/v1/tools")      # local tools registry (introspection only)
            or path.startswith("/v1/health")  # relay healthcheck
            or path.startswith("/schemas")    # OpenAPI schema for ChatGPT Actions / Plugins
            or path.startswith("/actions")    # ChatGPT Actions-only endpoints
            or path.startswith("/v1/v1/")     # guard against accidental double-prefixing
        )

        # All other /v1/* endpoints (including /v1/responses and its subroutes)
        # are forwarded unchanged to the upstream OpenAI API. This preserves
        # full compatibility with:
        #   • Responses API (tools, state, structured outputs)
        #   • Python SDK (client.responses.create, client.files.create, etc.)
        #   • Node SDK (client.responses.create, client.vectorStores.create, etc.)
        if not excluded and path.startswith("/v1/"):
            logger.info(f"🔄 Forwarding upstream: {method} {path}")
            return await forward_openai_request(request)

        # Anything outside /v1/* or explicitly excluded is handled locally.
        logger.info(f"⚙️ Handling locally: {method} {path}")
        response = await call_next(request)
        return response
