# app/core/http_client.py
from __future__ import annotations

import threading
from typing import Optional

from openai import OpenAI, AsyncOpenAI

from .config import get_settings


_client: Optional[OpenAI] = None
_async_client: Optional[AsyncOpenAI] = None
_lock = threading.Lock()


def get_openai_client() -> OpenAI:
    """
    Lazily instantiate and cache a single synchronous OpenAI client.

    Uses the official OpenAI SDK (v2.x), configured via Settings:
    api_key, base_url, organization, timeout, max_retries.
    """
    global _client
    if _client is None:
        with _lock:
            if _client is None:
                settings = get_settings()
                _client = OpenAI(
                    api_key=settings.openai_api_key,
                    base_url=settings.openai_base_url,
                    organization=settings.openai_organization,
                    timeout=settings.timeout_seconds,
                    max_retries=settings.max_retries,
                )
    return _client


def get_async_openai_client() -> AsyncOpenAI:
    """
    Lazily instantiate and cache a single asynchronous OpenAI client.
    """
    global _async_client
    if _async_client is None:
        with _lock:
            if _async_client is None:
                settings = get_settings()
                _async_client = AsyncOpenAI(
                    api_key=settings.openai_api_key,
                    base_url=settings.openai_base_url,
                    organization=settings.openai_organization,
                    timeout=settings.timeout_seconds,
                    max_retries=settings.max_retries,
                )
    return _async_client
