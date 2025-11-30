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

        def _get_float(attr: str, env_name: str, default: float) -> float:
            raw = _get(attr, env_name, default)
            try:
                return float(raw)
            except (TypeError, ValueError):
                return default

        # ----- resolve base URL & models -----------------------------------

        base = (
            openai_api_base
            or _get("OPENAI_API_BASE", "OPENAI_API_BASE", "https://api.openai.com/v1")
        )
        # Cast AnyHttpUrl → str so httpx.URL() is happy
        self.openai_api_base: str = str(base)

        self.default_model: str = (
            default_model
            or _get("DEFAULT_MODEL", "DEFAULT_MODEL", "gpt-4o-mini")
        )

        self.realtime_model: str = (
            realtime_model
            or _get("REALTIME_MODEL", "REALTIME_MODEL", "gpt-realtime")
        )

        # ----- streaming & chaining behaviour ------------------------------

        if enable_stream is None:
            raw_stream = str(_get("ENABLE_STREAM", "ENABLE_STREAM", "true")).lower()
            self.enable_stream: bool = raw_stream in {"1", "true", "yes", "on"}
        else:
            self.enable_stream = enable_stream

        self.chain_wait_mode: str = (
            chain_wait_mode
            or _get("CHAIN_WAIT_MODE", "CHAIN_WAIT_MODE", "sequential")
        )

        # ----- timeouts & relay identity -----------------------------------

        self.proxy_timeout: float = (
            proxy_timeout
            if proxy_timeout is not None
            else _get_float("PROXY_TIMEOUT", "PROXY_TIMEOUT", 30.0)
        )

        self.relay_timeout: float = (
            relay_timeout
            if relay_timeout is not None
            else _get_float("RELAY_TIMEOUT", "RELAY_TIMEOUT", 60.0)
        )

        self.relay_name: str = (
            relay_name
            or _get("RELAY_NAME", "RELAY_NAME", "chatgpt-team-relay")
        )

        # ----- AsyncOpenAI client ------------------------------------------

        api_key = getattr(settings, "OPENAI_API_KEY", os.getenv("OPENAI_API_KEY", ""))

        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=self.openai_api_base,
            timeout=self.proxy_timeout,
        )

        # Snapshot of config for routes/tools/tests to inspect
        self.p4_config: Dict[str, Any] = {
            "default_model": self.default_model,
            "realtime_model": self.realtime_model,
            "enable_stream": self.enable_stream,
            "chain_wait_mode": self.chain_wait_mode,
            "proxy_timeout": self.proxy_timeout,
            "relay_timeout": self.relay_timeout,
            "relay_name": self.relay_name,
            "app_mode": getattr(settings, "APP_MODE", "unknown"),
            "environment": getattr(settings, "ENVIRONMENT", "unknown"),
        }

        logger.info(
            "P4OrchestratorMiddleware initialized",
            extra=self.p4_config | {"openai_api_base": self.openai_api_base},
        )

    async def dispatch(self, request: Request, call_next):
        """
        Attach the shared OpenAI client + P4 config to request.state
        so downstream routes and agents can reuse them.
        """
        request.state.openai_client = self.client
        request.state.p4_config = self.p4_config

        response = await call_next(request)
        return response
