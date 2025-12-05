# app/core/http_client.py

from __future__ import annotations

from functools import lru_cache
from typing import Any, Dict

from openai import AsyncOpenAI, OpenAI  # OpenAI Python SDK v2 

from app.core.config import Settings, get_settings


def _client_kwargs(settings: Settings) -> Dict[str, Any]:
    kwargs: Dict[str, Any] = {
        "api_key": settings.openai_api_key,
        "base_url": settings.openai_base_url,
        "timeout": settings.timeout_seconds,
        "max_retries": settings.max_retries,
    }
    if settings.openai_organization:
        kwargs["organization"] = settings.openai_organization
    return kwargs


@lru_cache(maxsize=1)
def get_openai_client() -> OpenAI:
    """
    Lazily constructed sync OpenAI client shared across the process.
    """
    settings = get_settings()
    return OpenAI(**_client_kwargs(settings))


@lru_cache(maxsize=1)
def get_async_openai_client() -> AsyncOpenAI:
    """
    Lazily constructed async OpenAI client shared across the process.
    """
    settings = get_settings()
    return AsyncOpenAI(**_client_kwargs(settings))
