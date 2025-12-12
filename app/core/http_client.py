from __future__ import annotations

import asyncio
import weakref
from dataclasses import dataclass
from typing import Dict, Optional

import httpx
from openai import AsyncOpenAI

from app.core.config import settings


@dataclass
class _LoopClients:
    loop_ref: weakref.ReferenceType[asyncio.AbstractEventLoop]
    httpx_client: httpx.AsyncClient
    openai_client: AsyncOpenAI


# Keyed by id(loop). We keep a weakref to detect stale loops.
_LOOP_CLIENTS: Dict[int, _LoopClients] = {}


def _cleanup_stale_loops() -> None:
    stale: list[int] = []
    for key, entry in _LOOP_CLIENTS.items():
        loop = entry.loop_ref()
        if loop is None or loop.is_closed():
            stale.append(key)
    # Best-effort: we cannot safely await close here (sync function).
    # The next get() call will create fresh clients.
    for key in stale:
        _LOOP_CLIENTS.pop(key, None)


def _httpx_timeout() -> httpx.Timeout:
    # Keep conservative defaults; override in settings if you have fields.
    # If you already have settings like HTTPX_TIMEOUT_SECONDS, plug them in.
    return httpx.Timeout(60.0)


def get_async_httpx_client() -> httpx.AsyncClient:
    """
    Return an AsyncClient that is safe under pytest's function-scoped event loops.

    Why:
      - pytest-asyncio (STRICT) often creates a new loop per test.
      - Reusing a single global AsyncClient across loops can trigger
        'RuntimeError: Event loop is closed'. 
    """
    _cleanup_stale_loops()

    loop = asyncio.get_running_loop()
    key = id(loop)

    entry = _LOOP_CLIENTS.get(key)
    if entry is not None and not entry.httpx_client.is_closed:
        return entry.httpx_client

    client = httpx.AsyncClient(
        timeout=_httpx_timeout(),
        follow_redirects=True,
    )

    # OpenAI SDK client for this loop (base_url normalization handled in forwarder).
    openai_client = AsyncOpenAI(
        api_key=settings.openai_api_key,
        base_url=_sdk_base_url(str(settings.openai_base_url)),
    )

    _LOOP_CLIENTS[key] = _LoopClients(loop_ref=weakref.ref(loop), httpx_client=client, openai_client=openai_client)
    return client


def get_async_openai_client() -> AsyncOpenAI:
    _cleanup_stale_loops()

    loop = asyncio.get_running_loop()
    key = id(loop)

    entry = _LOOP_CLIENTS.get(key)
    if entry is not None:
        return entry.openai_client

    # Ensure both clients exist together.
    _ = get_async_httpx_client()
    return _LOOP_CLIENTS[key].openai_client


async def aclose_clients_for_current_loop() -> None:
    loop = asyncio.get_running_loop()
    key = id(loop)
    entry = _LOOP_CLIENTS.pop(key, None)
    if entry is None:
        return
    if not entry.httpx_client.is_closed:
        await entry.httpx_client.aclose()
    # AsyncOpenAI uses httpx under the hood; nothing extra required.


async def aclose_all_clients() -> None:
    entries = list(_LOOP_CLIENTS.items())
    _LOOP_CLIENTS.clear()
    for _, entry in entries:
        if not entry.httpx_client.is_closed:
            await entry.httpx_client.aclose()


def _sdk_base_url(base_url: str) -> str:
    """
    AsyncOpenAI expects a base_url that typically includes /v1.
    We accept either:
      - https://api.openai.com
      - https://api.openai.com/v1
    and normalize to .../v1
    """
    b = base_url.rstrip("/")
    if not b.endswith("/v1"):
        b = f"{b}/v1"
    return b
