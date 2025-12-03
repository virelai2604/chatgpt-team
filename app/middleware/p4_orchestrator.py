# app/middleware/p4_orchestrator.py

from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from openai import AsyncOpenAI

from app.core.config import settings

logger = logging.getLogger("p4_orchestrator")


class P4OrchestratorMiddleware(BaseHTTPMiddleware):
    """
    Central P4 orchestration middleware.

    Responsibilities:
    - Build a shared AsyncOpenAI client configured from settings/env.
    - Attach `openai_client` and `p4_config` to `request.state` for routes,
      tools, and agent workflows.
    - Do NOT modify path/body; this is orchestration context only.
    """

    def __init__(
        self,
        app: ASGIApp,
        *,
        openai_api_base: Optional[str] = None,
        default_model: Optional[str] = None,
        realtime_model: Optional[str] = None,
        enable_stream: Optional[bool] = None,
        chain_wait_mode: Optional[str] = None,
        proxy_timeout: Optional[float] = None,
        relay_timeout: Optional[float] = None,
        relay_name: Optional[str] = None,
    ) -> None:
        # IMPORTANT: keep BaseHTTPMiddleware init
        super().__init__(app)

        # ----- helpers -----------------------------------------------------

        def _get(attr: str, env_name: str, default: Any) -> Any:
            """
            Priority:
              1. settings.<attr> if present and not None
              2. environment variable <env_name>
              3. provided default
            """
            if hasattr(settings, attr):
                val = getattr(settings, attr)
                if val is not None:
                    return val

            env_val = os.getenv(env_name)
            if env_val is not None:
                return env_val

            return default

        # ----- resolve core config ----------------------------------------

        resolved_api_base = (
            openai_api_base
            or str(_get("OPENAI_API_BASE", "OPENAI_API_BASE", "https://api.openai.com"))
        )
        # normalize – no trailing slash
        self.openai_api_base: str = str(resolved_api_base).rstrip("/")

        self.default_model: str = default_model or str(
            _get("DEFAULT_MODEL", "DEFAULT_MODEL", "gpt-4o-mini")
        )
        self.realtime_model: str = realtime_model or str(
            _get("REALTIME_MODEL", "REALTIME_MODEL", "gpt-4.1-mini")
        )

        self.enable_stream: bool = (
            bool(_get("P4_ENABLE_STREAM", "P4_ENABLE_STREAM", True))
            if enable_stream is None
            else bool(enable_stream)
        )

        self.chain_wait_mode: str = chain_wait_mode or str(
            _get("P4_CHAIN_WAIT_MODE", "P4_CHAIN_WAIT_MODE", "sequential")
        )

        # Timeouts (seconds) – prefer explicit args, else env/settings
        proxy_timeout_val = (
            proxy_timeout
            if proxy_timeout is not None
            else _get("PROXY_TIMEOUT", "PROXY_TIMEOUT", settings.PROXY_TIMEOUT)
        )
        relay_timeout_val = (
            relay_timeout
            if relay_timeout is not None
            else _get("RELAY_TIMEOUT", "RELAY_TIMEOUT", settings.RELAY_TIMEOUT)
        )

        self.proxy_timeout: float = float(proxy_timeout_val)
        self.relay_timeout: float = float(relay_timeout_val)

        self.relay_name: str = relay_name or str(
            _get("RELAY_NAME", "RELAY_NAME", settings.RELAY_NAME)
        )

        # ----- build shared AsyncOpenAI client -----------------------------

        if not settings.OPENAI_API_KEY:
            logger.warning(
                "P4OrchestratorMiddleware: OPENAI_API_KEY is empty; "
                "upstream OpenAI calls will fail until configured."
            )

        # For openai-python 2.x, use `base_url` to point at REST root
        self.openai_client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=f"{self.openai_api_base}/v1",
        )

        # Snapshot config once; attach by reference on each request
        self.p4_config: Dict[str, Any] = {
            "openai_api_base": self.openai_api_base,
            "default_model": self.default_model,
            "realtime_model": self.realtime_model,
            "enable_stream": self.enable_stream,
            "chain_wait_mode": self.chain_wait_mode,
            "proxy_timeout": self.proxy_timeout,
            "relay_timeout": self.relay_timeout,
            "relay_name": self.relay_name,
            "environment": settings.ENVIRONMENT,
            "app_mode": settings.APP_MODE,
        }

        logger.info(
            "P4OrchestratorMiddleware configured "
            "(api_base=%s, default_model=%s, realtime_model=%s, relay_name=%s)",
            self.openai_api_base,
            self.default_model,
            self.realtime_model,
            self.relay_name,
        )

    async def dispatch(self, request: Request, call_next):
        """
        Attach the shared AsyncOpenAI client + config onto request.state.
        Do not mutate the path/body; just enrich context for downstream.
        """
        request.state.openai_client = self.openai_client
        request.state.p4_config = self.p4_config
        return await call_next(request)
