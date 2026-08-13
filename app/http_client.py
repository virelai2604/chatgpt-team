from __future__ import annotations

"""
Legacy re-export module.

Some earlier code imported `get_async_httpx_client` from `app.http_client`.
The canonical implementation lives in `app.core.http_client`.

This module also used to re-export `get_async_openai_client`, but no such
factory has ever existed in `app.core.http_client`, so importing this module
raised ImportError. The name is dropped rather than implemented: the relay is a
transparent proxy that forwards with its own httpx client and uses the OpenAI
SDK only for the `OpenAIError` exception type, so it has no SDK client to hand
out. See the openai 3.0 / HTTPX2 note in `pyproject.toml`.
"""

from app.core.http_client import get_async_httpx_client

__all__ = ["get_async_httpx_client"]
