from __future__ import annotations

"""
Legacy re-export module.

Some earlier code imported `get_async_httpx_client` from `app.http_client`.
The canonical implementation lives in `app.core.http_client`.

This module also used to re-export `get_async_openai_client`, which has no
implementation to point at: the relay forwards over its own httpx client and
never constructs an OpenAI/AsyncOpenAI client. Re-exporting it made this module
raise ImportError on import, so the dead name is gone.
"""

from app.core.http_client import get_async_httpx_client

__all__ = ["get_async_httpx_client"]
