from __future__ import annotations

"""Compatibility shim.

Historically some modules imported HTTP/OpenAI clients from app.utils.http_client.
The canonical implementation lives in app.core.http_client.

This module re-exports the public helpers to avoid churn.
"""

from app.core.http_client import (  # noqa: F401
    aclose_all_clients,
    close_async_clients,
    get_async_httpx_client,
    get_async_openai_client,
)

__all__ = [
    "get_async_httpx_client",
    "get_async_openai_client",
    "close_async_clients",
    "aclose_all_clients",
]


ModuleNotFoundError: No module named 'app.http_client'

and at "\\wsl.localhost\Ubuntu\home\user\code\chatgpt-team\app\core\http_client.py"

from __future__ import annotations

import asyncio
from typing import Dict, Optional, Tuple

import httpx
from openai import AsyncOpenAI

from app.core.config import get_settings
from app.utils.logger import get_logger

log = get_logger(__name__)

# Cache per-event-loop AND per-timeout to avoid:
# - "attached to a different loop" issues with reload
# - unintended timeout coupling between routes (SSE vs non-SSE)
_LOOP_CLIENTS: Dict[Tuple[int, float], Tuple[httpx.AsyncClient, AsyncOpenAI]] = {}


def _loop_id() -> int:
    try:
        return id(asyncio.get_running_loop())
    except RuntimeError:
        # No running loop (import-time / sync context). Use a stable sentinel.
        return -1


def _normalize_timeout_seconds(timeout_s: float) -> float:
    # Make float keys stable (avoid 120 vs 120.0 vs 120.0000001)
    return float(f"{float(timeout_s):.6f}")


def get_async_httpx_client(timeout: Optional[float] = None) -> httpx.AsyncClient:
    settings = get_settings()
    effective_timeout = (
        float(timeout)
        if timeout is not None
        else float(getattr(settings, "proxy_timeout_seconds", 120.0))
    )
    effective_timeout = _normalize_timeout_seconds(effective_timeout)

    key = (_loop_id(), effective_timeout)
    if key in _LOOP_CLIENTS:
        return _LOOP_CLIENTS[key][0]

    client_timeout = httpx.Timeout(effective_timeout)
    client = httpx.AsyncClient(timeout=client_timeout)

    openai_client = AsyncOpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        http_client=client,
    )

    _LOOP_CLIENTS[key] = (client, openai_client)
    return client


def get_async_openai_client(timeout: Optional[float] = None) -> AsyncOpenAI:
    settings = get_settings()
    effective_timeout = (
        float(timeout)
        if timeout is not None
        else float(getattr(settings, "proxy_timeout_seconds", 120.0))
    )
    effective_timeout = _normalize_timeout_seconds(effective_timeout)

    key = (_loop_id(), effective_timeout)
    if key in _LOOP_CLIENTS:
        return _LOOP_CLIENTS[key][1]

    # Ensure both are created together (shared httpx client)
    get_async_httpx_client(timeout=effective_timeout)
    return _LOOP_CLIENTS[key][1]


async def close_async_clients() -> None:
    """Close the cached clients for the current event loop (all timeouts)."""
    loop_key = _loop_id()
    keys = [k for k in _LOOP_CLIENTS.keys() if k[0] == loop_key]
    for k in keys:
        client, _ = _LOOP_CLIENTS.pop(k)
        try:
            await client.aclose()
        except Exception:
            log.exception("Failed closing httpx client (loop=%s, timeout=%s)", k[0], k[1])


async def aclose_all_clients() -> None:
    """Close all cached clients across loops (best-effort)."""
    items = list(_LOOP_CLIENTS.items())
    _LOOP_CLIENTS.clear()
    for (loop_id, timeout_s), (client, _) in items:
        try:
            await client.aclose()
        except Exception:
            log.exception("Failed closing httpx client (loop=%s, timeout=%s)", loop_id, timeout_s)

