from __future__ import annotations

"""
Compatibility shim.

Some modules historically imported HTTP/OpenAI clients from `app.http_client`.
The canonical implementation lives in `app.core.http_client` (and is also re-exported
from `app.utils.http_client`).

This module exists to keep legacy imports working.
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
