from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from fastapi import Request
from openai import AsyncOpenAI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

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
        super().__init__(app)

        base = openai_api_base or str(settings.OPENAI_API_BASE)
        self.openai_api_base: str = base.rstrip("/")

        self.default_model: str = default_model or settings.DEFAULT_MODEL
        self.realtime_model: str = realtime_model or settings.REALTIME_MODEL

        if enable_stream is None:
            self.enable_stream: bool = True
        else:
            self.enable_stream = enable_stream

        self.chain_wait_mode: str = chain_wait_mode or "sequential"
        self.proxy_timeout: float = float(proxy_timeout or settings.PROXY_TIMEOUT)
        self.relay_timeout: float = float(relay_timeout or settings.RELAY_TIMEOUT)
        self.relay_name: str = relay_name or settings.RELAY_NAME

        # Shared AsyncOpenAI client for agent workflows (not used by HTTP proxy).
        self.openai_client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=self.openai_api_base,
        )

        logger.info(
            "P4OrchestratorMiddleware configured: base=%s, default_model=%s, realtime_model=%s",
            self.openai_api_base,
            self.default_model,
            self.realtime_model,
        )

    async def dispatch(self, request: Request, call_next):
        # Attach orchestration context to request.state for downstream use.
        p4_config: Dict[str, Any] = {
            "openai_api_base": self.openai_api_base,
            "default_model": self.default_model,
            "realtime_model": self.realtime_model,
            "enable_stream": self.enable_stream,
            "chain_wait_mode": self.chain_wait_mode,
            "proxy_timeout": self.proxy_timeout,
            "relay_timeout": self.relay_timeout,
            "relay_name": self.relay_name,
        }

        request.state.openai_client = self.openai_client
        request.state.p4_config = p4_config

        return await call_next(request)
