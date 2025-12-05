# app/core/http_client.py
from typing import Optional
import threading

import httpx
from openai import OpenAI

from .config import get_settings

_client: Optional[OpenAI] = None
_lock = threading.Lock()


def get_openai_client() -> OpenAI:
    """
    Lazily instantiate and cache a single OpenAI client configured
    from environment-backed settings.
    """
    global _client
    if _client is None:
        with _lock:
            if _client is None:
                settings = get_settings()
                timeout = httpx.Timeout(settings.timeout_seconds)
                _client = OpenAI(
                    api_key=settings.openai_api_key,
                    base_url=settings.openai_base_url,
                    organization=settings.openai_organization,
                    timeout=timeout,
                    max_retries=settings.max_retries,
                )
    return _client
