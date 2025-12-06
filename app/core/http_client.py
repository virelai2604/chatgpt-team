# app/core/http_client.py
from typing import Optional
import threading

import httpx
from openai import OpenAI, AsyncOpenAI

from app.core.config import get_settings


_sync_client: Optional[OpenAI] = None
_async_client: Optional[AsyncOpenAI] = None
_lock = threading.Lock()


def _build_timeout(seconds: float) -> httpx.Timeout:
    """
    Build an httpx.Timeout from a single float.
    Applies to connect/read/write/pool uniformly.
    """
    return httpx.Timeout(seconds)


def _ensure_api_key() -> str:
    """
    Fetch OPENAI_API_KEY from settings and raise a clear error if missing.
    This avoids cryptic failures inside the SDK.
    """
    settings = get_settings()
    if not settings.openai_api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not configured. "
            "Set it in your environment or .env file before starting the relay."
        )
    return settings.openai_api_key


def get_openai_client() -> OpenAI:
    """
    Lazily instantiate and cache a single synchronous OpenAI client.
    This is used by non-async routes (e.g., /v1/responses when not streaming).
    """
    global _sync_client
    if _sync_client is None:
        with _lock:
            if _sync_client is None:
                settings = get_settings()
                api_key = _ensure_api_key()
                timeout = _build_timeout(settings.timeout_seconds)

                _sync_client = OpenAI(
                    api_key=api_key,
                    base_url=settings.openai_base_url,
                    organization=settings.openai_organization,
                    timeout=timeout,
                    max_retries=settings.max_retries,
                )

    return _sync_client


def get_async_openai_client() -> AsyncOpenAI:
    """
    Lazily instantiate and cache a single AsyncOpenAI client.
    This is used by streaming/SSE routes and any async flows.
    """
    global _async_client
    if _async_client is None:
        with _lock:
            if _async_client is None:
                settings = get_settings()
                api_key = _ensure_api_key()
                timeout = _build_timeout(settings.timeout_seconds)

                _async_client = AsyncOpenAI(
                    api_key=api_key,
                    base_url=settings.openai_base_url,
                    organization=settings.openai_organization,
                    timeout=timeout,
                    max_retries=settings.max_retries,
                )

    return _async_client
