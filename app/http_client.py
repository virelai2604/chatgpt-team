"""
Compatibility shim for legacy imports.

Some modules historically imported client helpers from `app.http_client`.
The canonical implementations live in `app.core.http_client`.

This module re-exports the public helpers to avoid churn and circular edits.
"""

from __future__ import annotations

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
