# app/core/http_client.py
from __future__ import annotations

import os
from typing import Optional

import httpx
from openai import AsyncOpenAI

from app.core.config import settings


def _float_env(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return float(default)
    return float(raw)


def _build_timeout() -> httpx.Timeout:
    # Prefer OPENAI_* env vars; fall back to Settings; and finally fall back to RELAY_TIMEOUT.
    relay_default = float(getattr(settings, "RELAY_TIMEOUT", 60.0))
    total = _float_env("OPENAI_TIMEOUT", getattr(settings, "OPENAI_TIMEOUT", relay_default))
    return httpx.Timeout(total)


_async_httpx_client: Optional[httpx.AsyncClient] = None
_async_openai_client: Optional[AsyncOpenAI] = None


def get_async_httpx_client() -> httpx.AsyncClient:
    """
    Shared AsyncClient for upstream proxying.
    """
    global _async_httpx_client
    if _async_httpx_client is None:
        _async_httpx_client = httpx.AsyncClient(
            timeout=_build_timeout(),
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
            follow_redirects=True,
        )
    return _async_httpx_client


def get_async_openai_client() -> AsyncOpenAI:
    """
    Shared OpenAI SDK client (async).
    Note: OpenAI Python SDK base_url defaults to https://api.openai.com/v1
    so it's OK if your settings.openai_base_url includes /v1.
    """
    global _async_openai_client
    if _async_openai_client is None:
        _async_openai_client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            timeout=_float_env("OPENAI_TIMEOUT", getattr(settings, "OPENAI_TIMEOUT", 60.0)),
        )
    return _async_openai_client
