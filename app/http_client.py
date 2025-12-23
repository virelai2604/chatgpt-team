from __future__ import annotations

"""Compatibility shim.

Historically some modules imported HTTP/OpenAI clients from `app.http_client`.
The canonical implementation lives in `app.core.http_client`.

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
