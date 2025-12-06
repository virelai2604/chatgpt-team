# app/core/http_client.py

from __future__ import annotations

from typing import Optional

from openai import AsyncOpenAI, OpenAI

from app.core.config import settings


def get_openai_client(api_key: Optional[str] = None) -> OpenAI:
    """
    Synchronous OpenAI client, using Settings as the single source of truth.
    """
    return OpenAI(
        api_key=api_key or settings.openai_api_key,
        base_url=settings.openai_base_url,
        organization=settings.openai_organization,
        max_retries=settings.max_retries,
        timeout=settings.timeout_seconds,
    )


def get_async_openai_client(api_key: Optional[str] = None) -> AsyncOpenAI:
    """
    Asynchronous OpenAI client for streaming / SSE use cases.
    """
    return AsyncOpenAI(
        api_key=api_key or settings.openai_api_key,
        base_url=settings.openai_base_url,
        organization=settings.openai_organization,
        max_retries=settings.max_retries,
        timeout=settings.timeout_seconds,
    )
