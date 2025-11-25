# app/middleware/p4_orchestrator.py

from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp, Message

from openai import AsyncOpenAI

from app.core.config import settings

logger = logging.getLogger("p4_orchestrator")


class P4OrchestratorMiddleware(BaseHTTPMiddleware):
    """
    Middleware that prepares a shared AsyncOpenAI client and per-request
    P4 config so route handlers can be thin wrappers.

    It does NOT change the path or body; it only attaches:
      - request.state.openai_client
      - request.state.p4_config
    """

    def __init__(
        self,
        app: ASGIApp,
        *,
        openai_api_base: str,
        default_model: str,
        realtime_model: str,
        enable_stream: bool,
        chain_wait_mode: str,
        proxy_timeout: int,
        relay_timeout: int,
        relay_name: str,
    ) -> None:
        super().__init__(app)

        self.client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=openai_api_base,
            timeout=proxy_timeout,
        )

        self.p4_config: Dict[str, Any] = {
            "default_model": default_model,
            "realtime_model": realtime_model,
            "enable_stream": enable_stream,
            "chain_wait_mode": chain_wait_mode,
            "proxy_timeout": proxy_timeout,
            "relay_timeout": relay_timeout,
            "relay_name": relay_name,
        }

        logger.info(
            "P4OrchestratorMiddleware initialized",
            extra={
                "openai_api_base": openai_api_base,
                "default_model": default_model,
                "realtime_model": realtime_model,
                "enable_stream": enable_stream,
                "chain_wait_mode": chain_wait_mode,
                "proxy_timeout": proxy_timeout,
                "relay_timeout": relay_timeout,
                "app_mode": settings.APP_MODE,
            },
        )

    async def dispatch(self, request: Request, call_next):
        # Attach client + config to request.state
        request.state.openai_client = self.client
        request.state.p4_config = self.p4_config

        response = await call_next(request)
        return response
