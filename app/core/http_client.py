from __future__ import annotations

import asyncio
from typing import Optional

import httpx

from app.core.settings import get_settings

_async_httpx_client: Optional[httpx.AsyncClient] = None
_async_httpx_client_loop_id: Optional[int] = None


def get_async_httpx_client(*, timeout_seconds: float | None = None, timeout: float | None = None) -> httpx.AsyncClient:
    """
    Return a shared httpx.AsyncClient.

    Compatibility:
      - Some routes call get_async_httpx_client(timeout=...)
      - Other routes call get_async_httpx_client(timeout_seconds=...)

    We accept both and set the client timeout only at first construction.
    Per-request timeouts should be passed to client.request(..., timeout=...).
    """
    global _async_httpx_client, _async_httpx_client_loop_id

    # Prefer timeout_seconds; fall back to timeout; then Settings; then a safe default.
    settings = get_settings()
    initial_timeout = (
        timeout_seconds
        if timeout_seconds is not None
        else timeout
        if timeout is not None
        else getattr(settings, "timeout_seconds", None)
        if getattr(settings, "timeout_seconds", None) is not None
        else 60.0
    )

    try:
        loop_id = id(asyncio.get_running_loop())
    except RuntimeError:
        loop_id = None

    if _async_httpx_client is None or _async_httpx_client.is_closed or _async_httpx_client_loop_id != loop_id:
        _async_httpx_client = httpx.AsyncClient(
            timeout=httpx.Timeout(float(initial_timeout)),
            follow_redirects=False,
        )
        _async_httpx_client_loop_id = loop_id
        
    return _async_httpx_client
