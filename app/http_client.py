from __future__ import annotations

"""
Legacy re-export module.

Some earlier code imported `get_async_httpx_client` / `get_async_openai_client` from `app.http_client`.
The canonical implementation lives in `app.core.http_client`.
"""

from app.core.http_client import get_async_httpx_client, get_async_openai_client

__all__ = ["get_async_httpx_client", "get_async_openai_client"]
