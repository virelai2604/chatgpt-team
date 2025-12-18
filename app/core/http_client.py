from __future__ import annotations

import asyncio
from typing import Any, Dict, Tuple

import httpx
from openai import AsyncOpenAI

from app.core.config import get_settings
from app.utils.logger import get_logger

log = get_logger(__name__)

# Cache per-event-loop to avoid "attached to a different loop" issues with reload.
_LOOP_CLIENTS: Dict[int, Tuple[httpx.AsyncClient, AsyncOpenAI]] = {}


def _loop_id() -> int:
    try:
        return id(asyncio.get_running_loop())
    except RuntimeError:
        # No running loop (import-time / sync context). Use a stable sentinel.
        return -1


def get_async_httpx_client() -> httpx.AsyncClient:
    loop_key = _loop_id()
    if loop_key in _LOOP_CLIENTS:
        return _LOOP_CLIENTS[loop_key][0]

    settings = get_settings()
    timeout = httpx.Timeout(getattr(settings, "relay_timeout_seconds", 120.0))
    client = httpx.AsyncClient(timeout=timeout)
    openai_client = AsyncOpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        http_client=client,
    )
    _LOOP_CLIENTS[loop_key] = (client, openai_client)
    return client


def get_async_openai_client() -> AsyncOpenAI:
    loop_key = _loop_id()
    if loop_key in _LOOP_CLIENTS:
        return _LOOP_CLIENTS[loop_key][1]

    # Ensure both are created together (shared httpx client)
    get_async_httpx_client()
    return _LOOP_CLIENTS[loop_key][1]


async def close_async_clients() -> None:
    """Close the cached clients for the current event loop."""
    loop_key = _loop_id()
    if loop_key not in _LOOP_CLIENTS:
        return

    client, _ = _LOOP_CLIENTS.pop(loop_key)
    try:
        await client.aclose()
    except Exception:
        log.exception("Failed closing httpx client")


async def aclose_all_clients() -> None:
    """Close all cached clients across loops (best-effort)."""
    items = list(_LOOP_CLIENTS.items())
    _LOOP_CLIENTS.clear()
    for _, (client, _) in items:
        try:
            await client.aclose()
        except Exception:
            log.exception("Failed closing httpx client")
