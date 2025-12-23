from __future__ import annotations

import asyncio
from typing import Dict, Optional, Tuple

import httpx
from openai import AsyncOpenAI

from app.core.config import get_settings

# Loop-local caches: each running event loop gets its own clients.
_LOOP_CLIENTS: Dict[int, Tuple[AsyncOpenAI, httpx.AsyncClient]] = {}


def _loop_id() -> int:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # No running loop; fall back to current loop (best effort).
        loop = asyncio.get_event_loop()
    return id(loop)


def get_async_openai_client(*, timeout: Optional[float] = None) -> AsyncOpenAI:
    """
    Return an AsyncOpenAI client that shares a loop-local httpx.AsyncClient.

    Optional:
      - timeout: override the httpx timeout (seconds) for this loop's shared client.
    """
    openai_client, _ = _get_or_create_clients(timeout=timeout)
    return openai_client


def get_async_httpx_client(*, timeout: Optional[float] = None) -> httpx.AsyncClient:
    """
    Return a loop-local shared httpx.AsyncClient.

    Optional:
      - timeout: override the client's timeout (seconds). If the client already exists,
        we update its timeout best-effort.
    """
    _, http_client = _get_or_create_clients(timeout=timeout)
    if timeout is not None:
        # Best-effort update; safe even if httpx internals change.
        try:
            http_client.timeout = httpx.Timeout(timeout)
        except Exception:
            pass
    return http_client


def _get_or_create_clients(*, timeout: Optional[float]) -> Tuple[AsyncOpenAI, httpx.AsyncClient]:
    lid = _loop_id()
    if lid in _LOOP_CLIENTS:
        return _LOOP_CLIENTS[lid]

    settings = get_settings()

    timeout_s = float(timeout) if timeout is not None else float(getattr(settings, "relay_timeout_seconds", 120.0))
    http_client = httpx.AsyncClient(timeout=httpx.Timeout(timeout_s))

    openai_client = AsyncOpenAI(
        api_key=settings.openai_api_key,
        base_url=getattr(settings, "openai_base_url", None) or "https://api.openai.com/v1",
        http_client=http_client,
    )

    _LOOP_CLIENTS[lid] = (openai_client, http_client)
    return openai_client, http_client


async def close_async_clients() -> None:
    """
    Close all loop-local clients (safe to call at shutdown).
    """
    for lid, (openai_client, http_client) in list(_LOOP_CLIENTS.items()):
        try:
            # OpenAI client uses the same http client; closing httpx is sufficient.
            await http_client.aclose()
        finally:
            _LOOP_CLIENTS.pop(lid, None)


async def aclose_all_clients() -> None:
    # Back-compat alias
    await close_async_clients()
