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
      • If path starts with /v1/ AND is NOT in the excluded set,
        forward to OpenAI via forward_openai_request.
      • Otherwise, let FastAPI handle it with local routes.
    """

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        method = request.method

        # Local-only or "special" routes that should NOT be proxied
        excluded = (
            path.startswith("/v1/tools")      # local tools registry
            or path.startswith("/v1/health")  # relay healthcheck
            or path.startswith("/schemas")    # OpenAPI schema for Actions/Plugins
            or path.startswith("/actions")    # ChatGPT Actions-only endpoints
            or path.startswith("/v1/v1/")     # guard against double-prefix
            or path.startswith("/v1/responses")  # local /v1/responses (if implemented)
        )

        if not excluded and path.startswith("/v1/"):
            logger.info(f"🔄 Forwarding upstream: {method} {path}")
            return await forward_openai_request(request)

        logger.info(f"⚙️ Handling locally: {method} {path}")
        response = await call_next(request)
        return response
