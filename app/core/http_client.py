from __future__ import annotations

from typing import Optional

import httpx
from openai import AsyncOpenAI

from app.core.config import settings


# Cache a small number of clients so tests (and callers) can vary timeouts
# without constantly rebuilding connection pools.
_httpx_clients: dict[float, httpx.AsyncClient] = {}
_openai_clients: dict[float, AsyncOpenAI] = {}


def get_async_httpx_client(
    *,
    timeout_seconds: Optional[float] = None,
    timeout: Optional[float] = None,
) -> httpx.AsyncClient:
    """
    Shared httpx.AsyncClient for outbound relay calls.

    Back-compat: accepts either `timeout_seconds=` (preferred) or `timeout=`.
    """
    eff = timeout_seconds if timeout_seconds is not None else timeout
    if eff is None:
        eff = float(getattr(settings, "PROXY_TIMEOUT_SECONDS", 90.0))
    eff_f = float(eff)

    client = _httpx_clients.get(eff_f)
    if client is None:
        # Do not set base_url here; forwarders construct absolute URLs explicitly.
        client = httpx.AsyncClient(timeout=eff_f)
        _httpx_clients[eff_f] = client
    return client


def get_async_openai_client(
    *,
    timeout_seconds: Optional[float] = None,
    timeout: Optional[float] = None,
) -> AsyncOpenAI:
    """
    AsyncOpenAI client for server-side helper calls (legacy snapshots).

    Most of the relay forwards requests via httpx, but a few routes use the OpenAI
    Python SDK for typed responses (e.g., embeddings). This shim keeps imports stable.
    """
    eff = timeout_seconds if timeout_seconds is not None else timeout
    if eff is None:
        eff = float(getattr(settings, "PROXY_TIMEOUT_SECONDS", 90.0))
    eff_f = float(eff)

    client = _openai_clients.get(eff_f)
    if client is None:
        base_url = (
            getattr(settings, "openai_base_url", None)
            or getattr(settings, "OPENAI_API_BASE", None)
            or "https://api.openai.com/v1"
        )
        api_key = getattr(settings, "OPENAI_API_KEY", "") or getattr(settings, "openai_api_key", "")
        http_client = get_async_httpx_client(timeout_seconds=eff_f)
        client = AsyncOpenAI(api_key=api_key, base_url=str(base_url), http_client=http_client)
        _openai_clients[eff_f] = client
    return client
