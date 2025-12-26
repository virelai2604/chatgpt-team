"""
Compatibility layer for older imports.

Preferred imports live under app.core.http_client, but some modules/tests import from app.http_client.
"""

from __future__ import annotations

try:
    from app.core.http_client import get_async_httpx_client, get_async_openai_client
except Exception:  # pragma: no cover
    # Fallback for older layouts
    from app.utils.http_client import get_async_httpx_client, get_async_openai_client  # type: ignore

__all__ = ["get_async_httpx_client", "get_async_openai_client"]
