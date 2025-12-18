from __future__ import annotations

"""app/utils/http_client.py

Compatibility shim.

Some older modules in this repo historically imported:

    from app.utils.http_client import get_client

The canonical implementation now lives in:

    app.core.http_client

This module preserves the old import path while keeping the actual
client lifecycle/behavior centralized in app.core.http_client.
"""

from typing import Any

import httpx

try:
    # OpenAI Python SDK (async)
    from openai import AsyncOpenAI  # type: ignore
except Exception:  # pragma: no cover
    AsyncOpenAI = Any  # type: ignore

from app.core.http_client import (
    aclose_all_clients,
    close_async_clients,
    get_async_httpx_client,
    get_async_openai_client,
)


def get_client() -> httpx.AsyncClient:
    """Backward-compatible alias for get_async_httpx_client()."""
    return get_async_httpx_client()


def get_openai_client() -> AsyncOpenAI:
    """Backward-compatible alias for get_async_openai_client()."""
    return get_async_openai_client()


__all__ = [
    "get_client",
    "get_openai_client",
    "get_async_httpx_client",
    "get_async_openai_client",
    "aclose_all_clients",
    "close_async_clients",
]
