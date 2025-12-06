# app/core/http_client.py

from __future__ import annotations

from functools import lru_cache
from typing import Any, Dict

from openai import OpenAI, AsyncOpenAI

from app.core.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


def _client_kwargs() -> Dict[str, Any]:
    """
    Build keyword arguments for OpenAI / AsyncOpenAI clients
    from the shared Settings object.
    """
    settings = get_settings()
    kwargs: Dict[str, Any] = {
        "api_key": settings.openai_api_key,
    }

    # The Python SDK supports overriding base_url and organization.
    if settings.openai_base_url:
        kwargs["base_url"] = settings.openai_base_url
    if getattr(settings, "openai_organization", None):
        kwargs["organization"] = settings.openai_organization

    # Optionally propagate timeout / retries if configured.
    timeout = getattr(settings, "timeout_seconds", None)
    if timeout is not None:
        kwargs["timeout"] = timeout

    max_retries = getattr(settings, "max_retries", None)
    if max_retries is not None:
        kwargs["max_retries"] = max_retries

    logger.debug(
        "Initializing OpenAI client with base_url=%s org=%s timeout=%s max_retries=%s",
        kwargs.get("base_url"),
        kwargs.get("organization"),
        kwargs.get("timeout"),
        kwargs.get("max_retries"),
    )
    return kwargs


@lru_cache(maxsize=1)
def get_openai_client() -> OpenAI:
    """
    Singleton synchronous OpenAI client.

    Use this for sync utilities or where FastAPI endpoints are sync.
    """
    return OpenAI(**_client_kwargs())


@lru_cache(maxsize=1)
def get_async_openai_client() -> AsyncOpenAI:
    """
    Singleton asynchronous OpenAI client.

    Use this from async FastAPI endpoints for better concurrency.
    """
    return AsyncOpenAI(**_client_kwargs())
