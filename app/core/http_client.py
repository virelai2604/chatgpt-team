from __future__ import annotations

import asyncio
from typing import Dict, Tuple, Optional

import httpx
from openai import AsyncOpenAI

from app.core.config import settings


# Cache clients per (event_loop_id, timeout_seconds) to avoid cross-loop usage.
_httpx_clients: Dict[Tuple[int, float], httpx.AsyncClient] = {}
_openai_clients: Dict[Tuple[int, float], AsyncOpenAI] = {}


def _loop_key() -> int:
    return id(asyncio.get_running_loop())


def _timeout_s(timeout_seconds: Optional[float]) -> float:
    return float(timeout_seconds if timeout_seconds is not None else settings.PROXY_TIMEOUT_SECONDS)


def get_async_httpx_client(*, timeout_seconds: Optional[float] = None) -> httpx.AsyncClient:
    """
    Shared AsyncClient for outbound calls to upstream.
    We do NOT set base_url here; callers should pass full URLs (safer).
    """
    t = _timeout_s(timeout_seconds)
    key = (_loop_key(), t)
    if key in _httpx_clients:
        return _httpx_clients[key]

    client = httpx.AsyncClient(
        timeout=httpx.Timeout(t),
        follow_redirects=True,
        headers={"User-Agent": "chatgpt-team-relay"},
    )
    _httpx_clients[key] = client
    return client


def get_async_openai_client(*, timeout_seconds: Optional[float] = None) -> AsyncOpenAI:
    """
    OpenAI SDK client for upstream calls when needed.
    Uses OPENAI_API_BASE (NOT OPENAI_BASE_URL).
    """
    t = _timeout_s(timeout_seconds)
    key = (_loop_key(), t)
    if key in _openai_clients:
        return _openai_clients[key]

    httpx_client = get_async_httpx_client(timeout_seconds=t)
    client = AsyncOpenAI(
        api_key=settings.OPENAI_API_KEY,
        base_url=settings.openai_base_url,
        http_client=httpx_client,
        timeout=t,
    )
    _openai_clients[key] = client
    return client
