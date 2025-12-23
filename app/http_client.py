from __future__ import annotations

# Keep legacy imports working without duplicating logic.
from app.core.http_client import (
    get_async_httpx_client,
    get_async_openai_client,
    close_async_clients,
)

__all__ = ["get_async_httpx_client", "get_async_openai_client", "close_async_clients"]
