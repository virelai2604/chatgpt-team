# app/core/http_client.py

from __future__ import annotations

import logging
import os
from functools import lru_cache
from typing import Optional

import httpx
from openai import OpenAI, AsyncOpenAI

from .config import settings

logger = logging.getLogger(__name__)

# Default OpenAI base URL if none is provided in settings
OPENAI_DEFAULT_BASE_URL = "https://api.openai.com/v1"


def _get_api_key() -> str:
    """
    Resolve the OpenAI API key.

    Priority:
      1. OPENAI_API_KEY environment variable
      2. settings.openai_api_key (new-style)
      3. settings.OPENAI_API_KEY (old-style)
    """
    key: Optional[str] = os.environ.get("OPENAI_API_KEY")

    if not key and hasattr(settings, "openai_api_key"):
        key = getattr(settings, "openai_api_key")

    if not key and hasattr(settings, "OPENAI_API_KEY"):
        key = getattr(settings, "OPENAI_API_KEY")

    if not key:
        logger.error("OPENAI_API_KEY is not set in environment or settings.")
        raise RuntimeError(
            "OPENAI_API_KEY is not set. "
            "Set it in your shell or ~/.env.secrets before starting the relay."
        )

    # Log only a short prefix for debugging; never the whole key.
    logger.debug("Using OPENAI_API_KEY prefix: %s********", key[:8])
    return key


def _get_base_url() -> str:
    """
    Resolve the OpenAI base URL from settings with several fallbacks.
    """
    for attr in ("openai_base_url", "OPENAI_BASE_URL", "OPENAI_API_BASE"):
        if hasattr(settings, attr):
            val = getattr(settings, attr)
            if val:
                return val

    return OPENAI_DEFAULT_BASE_URL


def _get_timeout_seconds() -> float:
    """
    Resolve timeout in seconds, with conservative defaults.
    """
    for attr in ("openai_timeout_seconds", "OPENAI_TIMEOUT_SECONDS"):
        if hasattr(settings, attr):
            try:
                value = float(getattr(settings, attr))
                if value > 0:
                    return value
            except (TypeError, ValueError):
                pass

    return 30.0


@lru_cache(maxsize=1)
def get_async_httpx_client() -> httpx.AsyncClient:
    """
    Shared async httpx client configured for talking directly to api.openai.com.
    Used by the generic forwarder (e.g. /v1/models).
    """
    headers = {
        "Authorization": f"Bearer {_get_api_key()}",
        "Content-Type": "application/json",
    }

    client = httpx.AsyncClient(
        base_url=_get_base_url(),
        headers=headers,
        timeout=_get_timeout_seconds(),
    )
    logger.debug(
        "Created shared AsyncClient for base_url=%s timeout=%s",
        client.base_url,
        client.timeout,
    )
    return client


@lru_cache(maxsize=1)
def get_openai_client() -> OpenAI:
    """
    Synchronous OpenAI client.

    We *do not* pass api_key here; we rely on the SDK reading OPENAI_API_KEY
    from the environment. We only override base_url if necessary.
    """
    kwargs = {}
    base_url = _get_base_url()
    if base_url and base_url != OPENAI_DEFAULT_BASE_URL:
        kwargs["base_url"] = base_url

    client = OpenAI(**kwargs)
    logger.debug(
        "Created OpenAI sync client with base_url=%s",
        base_url or OPENAI_DEFAULT_BASE_URL,
    )
    return client


@lru_cache(maxsize=1)
def get_async_openai_client() -> AsyncOpenAI:
    """
    Async OpenAI client.

    Same behavior as get_openai_client(): let the SDK read OPENAI_API_KEY
    from env, only override base_url if needed.
    """
    kwargs = {}
    base_url = _get_base_url()
    if base_url and base_url != OPENAI_DEFAULT_BASE_URL:
        kwargs["base_url"] = base_url

    client = AsyncOpenAI(**kwargs)
    logger.debug(
        "Created AsyncOpenAI client with base_url=%s",
        base_url or OPENAI_DEFAULT_BASE_URL,
    )
    return client
