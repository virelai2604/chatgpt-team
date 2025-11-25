"""
p4_orchestrator.py — Request Orchestration Middleware
──────────────────────────────────────────────────────
Decides whether a request should be handled locally by FastAPI
routes or forwarded upstream to the OpenAI API via forward_openai_request.
"""

from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable, Dict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.api.forward_openai import forward_openai_request

logger = logging.getLogger("p4_orchestrator")


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

    def __init__(
        self,
        app,
        *,
        openai_api_base: str | None = None,
        openai_api_key: str | None = None,
        default_model: str | None = None,
        assistants_beta: str | None = None,
        realtime_beta: str | None = None,
        enable_stream: bool | None = None,
        chain_wait_mode: str | None = None,
        app_mode: str | None = None,
        environment: str | None = None,
        tools_manifest: str | None = None,
        validation_schema_path: str | None = None,
        proxy_timeout: int | None = None,
        relay_timeout: int | None = None,
        **_: Any,
    ) -> None:
        """
        Accept configuration from FastAPI.add_middleware(**kwargs).

        We store these values on self so they can be used for logging,
        debugging, or passed downstream via request.state. The actual
        forwarding logic still lives in app.api.forward_openai.
        """
        super().__init__(app)

        self.openai_api_base = openai_api_base
        self.openai_api_key = openai_api_key
        self.default_model = default_model
        self.assistants_beta = assistants_beta
        self.realtime_beta = realtime_beta
        self.enable_stream = enable_stream
        self.chain_wait_mode = chain_wait_mode
        self.app_mode = app_mode
        self.environment = environment
        self.tools_manifest = tools_manifest
        self.validation_schema_path = validation_schema_path
        self.proxy_timeout = proxy_timeout
        self.relay_timeout = relay_timeout

        logger.info(
            "P4OrchestratorMiddleware initialized "
            "(config keys: openai_api_base, default_model, realtime_model, "
            "enable_stream, chain_wait_mode, proxy_timeout, relay_timeout, relay_name)",
            extra={
                "openai_api_base": self.openai_api_base,
                "default_model": self.default_model,
                "realtime_beta": self.realtime_beta,
                "enable_stream": self.enable_stream,
                "chain_wait_mode": self.chain_wait_mode,
                "proxy_timeout": self.proxy_timeout,
                "relay_timeout": self.relay_timeout,
                "environment": self.environment,
                "app_mode": self.app_mode,
            },
        )

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        path = request.url.path

        # Optionally expose config to downstream handlers (safe no-op if unused).
        try:
            request.state.relay_config = {
                "openai_api_base": self.openai_api_base,
                "default_model": self.default_model,
                "assistants_beta": self.assistants_beta,
                "realtime_beta": self.realtime_beta,
                "enable_stream": self.enable_stream,
                "chain_wait_mode": self.chain_wait_mode,
                "app_mode": self.app_mode,
                "environment": self.environment,
                "tools_manifest": self.tools_manifest,
                "validation_schema_path": self.validation_schema_path,
                "proxy_timeout": self.proxy_timeout,
                "relay_timeout": self.relay_timeout,
            }
        except Exception:
            # Never break requests just because of state wiring.
            pass

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

        # Known local routers (responses, conversations, files, etc.)
        # are already registered in main.py, so we allow FastAPI to resolve them.
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
