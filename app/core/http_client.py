from __future__ import annotations

import asyncio
import contextvars
from typing import Optional, Tuple

import httpx
from openai import AsyncOpenAI

from app.core.config import settings


_httpx_client_var: contextvars.ContextVar[Optional[Tuple[asyncio.AbstractEventLoop, httpx.AsyncClient]]] = (
    contextvars.ContextVar("httpx_async_client", default=None)
)
_openai_client_var: contextvars.ContextVar[Optional[Tuple[asyncio.AbstractEventLoop, AsyncOpenAI]]] = (
    contextvars.ContextVar("openai_async_client", default=None)
)


def _get_setting(*names: str, default=None):
    for name in names:
        if hasattr(settings, name):
            val = getattr(settings, name)
            if val is not None:
                return val
    return default


def _default_timeout_s() -> float:
    # Support multiple historical config names.
    return float(
        _get_setting(
            "RELAY_TIMEOUT",
            "RELAY_TIMEOUT_S",
            "OPENAI_TIMEOUT",
            "OPENAI_TIMEOUT_S",
            default=60.0,
        )
    )


def get_async_httpx_client(timeout: Optional[float] = None) -> httpx.AsyncClient:
    """
    Canonical shared AsyncClient (per event loop).
    """
    loop = asyncio.get_running_loop()
    cached = _httpx_client_var.get()
    if cached and cached[0] is loop:
        return cached[1]

    t = float(timeout) if timeout is not None else _default_timeout_s()

    client = httpx.AsyncClient(
        timeout=httpx.Timeout(t),
        limits=httpx.Limits(max_connections=200, max_keepalive_connections=50),
        follow_redirects=True,
    )
    _httpx_client_var.set((loop, client))
    return client


def get_async_openai_client() -> AsyncOpenAI:
    """
    Canonical shared AsyncOpenAI client (per event loop).
    """
    loop = asyncio.get_running_loop()
    cached = _openai_client_var.get()
    if cached and cached[0] is loop:
        return cached[1]

    api_key = _get_setting("OPENAI_API_KEY", "openai_api_key")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured.")

    base_url = _get_setting(
        "OPENAI_BASE_URL",
        "OPENAI_API_BASE",
        "openai_base_url",
        "openai_api_base",
        default="https://api.openai.com/v1",
    )

    organization = _get_setting("OPENAI_ORG", "OPENAI_ORGANIZATION", "openai_organization")
    project = _get_setting("OPENAI_PROJECT", "openai_project")

    # Reuse our HTTPX pool for upstream calls.
    http_client = get_async_httpx_client()

    client = AsyncOpenAI(
        api_key=api_key,
        base_url=base_url,
        organization=organization,
        project=project,
        http_client=http_client,
    )

    _openai_client_var.set((loop, client))
    return client
