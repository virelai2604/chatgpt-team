from __future__ import annotations

"""
Canonical HTTP/OpenAI client factory for the relay.

Design goals:
- One pooled httpx AsyncClient per (event loop, timeout) for upstream forwarding
- One pooled OpenAI AsyncOpenAI per (event loop, timeout) for SDK-style calls
- Safe cleanup for reload/shutdown

IMPORTANT:
Do not paste terminal tracebacks into this file. A single stray line like:
    ModuleNotFoundError: ...
will cause a SyntaxError and prevent Uvicorn from importing the app.
"""

import asyncio
from typing import Dict, Optional, Tuple, cast

import httpx
from openai import AsyncOpenAI, DefaultAsyncHttpxClient

from app.core.config import settings
from app.utils.logger import get_logger

log = get_logger(__name__)

# Keyed by (id(loop), timeout_seconds)
_HTTPX_CLIENTS: Dict[Tuple[int, float], httpx.AsyncClient] = {}
_OPENAI_CLIENTS: Dict[Tuple[int, float], AsyncOpenAI] = {}

_lock = asyncio.Lock()


def _get_setting(name_snake: str, name_upper: str, default=None):
    """
    Read a setting from either snake_case or UPPER_CASE attributes.
    """
    if hasattr(settings, name_snake):
        return getattr(settings, name_snake)
    if hasattr(settings, name_upper):
        return getattr(settings, name_upper)
    return default


def _default_timeout_seconds() -> float:
    # Prefer PROXY timeout for relay->OpenAI forwarding.
    v = _get_setting("proxy_timeout_seconds", "PROXY_TIMEOUT_SECONDS", None)
    if v is None:
        v = _get_setting("relay_timeout_seconds", "RELAY_TIMEOUT_SECONDS", 90)
    try:
        return float(v)
    except Exception:
        return 90.0


def _normalize_base_url_for_sdk(base_url: str) -> str:
    """
    The OpenAI SDK expects base_url ending with /v1 (it will append endpoint paths like /responses).
    """
    b = (base_url or "").strip()
    if not b:
        return "https://api.openai.com/v1"
    b = b.rstrip("/")
    if b.endswith("/v1"):
        return b
    return f"{b}/v1"


def _loop_id() -> int:
    return id(asyncio.get_running_loop())


async def get_async_httpx_client(timeout_s: Optional[float] = None) -> httpx.AsyncClient:
    """
    Shared httpx client for forwarding relay requests upstream.
    """
    t = float(timeout_s) if timeout_s is not None else _default_timeout_seconds()
    key = (_loop_id(), t)

    async with _lock:
        client = _HTTPX_CLIENTS.get(key)
        if client is not None:
            return client

        timeout = httpx.Timeout(t)
        client = httpx.AsyncClient(timeout=timeout)
        _HTTPX_CLIENTS[key] = client
        return client


async def get_async_openai_client(timeout_s: Optional[float] = None) -> AsyncOpenAI:
    """
    Shared OpenAI SDK client (AsyncOpenAI). Uses its own DefaultAsyncHttpxClient.
    """
    t = float(timeout_s) if timeout_s is not None else _default_timeout_seconds()
    key = (_loop_id(), t)

    async with _lock:
        client = _OPENAI_CLIENTS.get(key)
        if client is not None:
            return client

        api_key = cast(
            str,
            _get_setting("openai_api_key", "OPENAI_API_KEY", None),
        )
        api_base = cast(
            str,
            _get_setting("openai_api_base", "OPENAI_API_BASE", "https://api.openai.com/v1"),
        )
        organization = _get_setting("openai_organization", "OPENAI_ORGANIZATION", None)

        # Optional: combine beta headers if present
        assistants_beta = _get_setting("openai_assistants_beta", "OPENAI_ASSISTANTS_BETA", None)
        realtime_beta = _get_setting("openai_realtime_beta", "OPENAI_REALTIME_BETA", None)
        betas = [b for b in [assistants_beta, realtime_beta] if b]
        default_headers = {}
        if betas:
            default_headers["OpenAI-Beta"] = ",".join(betas)

        http_client = DefaultAsyncHttpxClient(timeout=httpx.Timeout(t))

        client = AsyncOpenAI(
            api_key=api_key,
            base_url=_normalize_base_url_for_sdk(api_base),
            organization=organization,
            default_headers=default_headers or None,
            http_client=http_client,
        )
        _OPENAI_CLIENTS[key] = client
        return client


async def close_async_clients() -> None:
    """
    Close and clear all cached clients for the current process.
    Useful on shutdown and reload.
    """
    async with _lock:
        openai_items = list(_OPENAI_CLIENTS.items())
        httpx_items = list(_HTTPX_CLIENTS.items())
        _OPENAI_CLIENTS.clear()
        _HTTPX_CLIENTS.clear()

    # Close OpenAI clients (their internal http_client) first.
    for (loop_id, timeout_s), client in openai_items:
        try:
            await client.close()
        except Exception:
            log.exception("Failed closing OpenAI client loop=%s timeout=%s", loop_id, timeout_s)

    # Close httpx clients used for forwarding.
    for (loop_id, timeout_s), client in httpx_items:
        try:
            await client.aclose()
        except Exception:
            log.exception("Failed closing httpx client loop=%s timeout=%s", loop_id, timeout_s)


async def aclose_all_clients() -> None:
    """
    Backwards-compatible alias.
    """
    await close_async_clients()


__all__ = [
    "get_async_httpx_client",
    "get_async_openai_client",
    "close_async_clients",
    "aclose_all_clients",
]
