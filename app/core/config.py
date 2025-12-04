from __future__ import annotations

import platform
from functools import lru_cache
from typing import Optional

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central configuration for the ChatGPT Team Relay.

    All values are loaded from environment variables or `.env`.
    Compatible with pydantic v2 + pydantic-settings v2.
    """

    # ------------------------------------------------------------------
    # Core relay / app mode
    # ------------------------------------------------------------------
    ENVIRONMENT: str = Field(default="local", alias="ENVIRONMENT")
    APP_MODE: str = Field(default="development", alias="APP_MODE")

    # ------------------------------------------------------------------
    # OpenAI upstream config
    # ------------------------------------------------------------------
    # IMPORTANT: do NOT include a `/v1` suffix here.
    # The HTTP client / AsyncOpenAI config adds `/v1` as needed.
    OPENAI_API_BASE: AnyHttpUrl = Field(
        default="https://api.openai.com",
        alias="OPENAI_API_BASE",
    )
    OPENAI_API_KEY: str = Field(
        default="",
        alias="OPENAI_API_KEY",
    )

    # Default models (used by P4OrchestratorMiddleware and Realtime)
    DEFAULT_MODEL: str = Field(
        default="gpt-5.1",
        alias="DEFAULT_MODEL",
    )
    REALTIME_MODEL: str = Field(
        default="gpt-4o-realtime-preview",
        alias="REALTIME_MODEL",
    )

    # Beta headers
    OPENAI_ASSISTANTS_BETA: str = Field(
        default="assistants=v2",
        alias="OPENAI_ASSISTANTS_BETA",
    )
    OPENAI_REALTIME_BETA: str = Field(
        default="realtime=v1",
        alias="OPENAI_REALTIME_BETA",
    )

    # ------------------------------------------------------------------
    # Relay identity / auth
    # ------------------------------------------------------------------
    RELAY_NAME: str = Field(
        default="ChatGPT Team Relay",
        alias="RELAY_NAME",
    )

    RELAY_AUTH_ENABLED: bool = Field(
        default=False,
        alias="RELAY_AUTH_ENABLED",
    )
    RELAY_KEY: Optional[str] = Field(
        default=None,
        alias="RELAY_KEY",
    )

    # Optional external hostname (used for metadata / logging / local dev)
    RELAY_HOST: Optional[str] = Field(
        default="0.0.0.0",
        alias="RELAY_HOST",
    )

    # ------------------------------------------------------------------
    # CORS configuration
    # ------------------------------------------------------------------
    # These are CSV strings, parsed by app/main.py via _split_csv().
    CORS_ALLOW_ORIGINS: str = Field(
        default="https://chat.openai.com,https://platform.openai.com",
        alias="CORS_ALLOW_ORIGINS",
    )
    CORS_ALLOW_METHODS: str = Field(
        default="GET,POST,PUT,PATCH,DELETE,OPTIONS",
        alias="CORS_ALLOW_METHODS",
    )
    CORS_ALLOW_HEADERS: str = Field(
        default="Authorization,Content-Type,Accept",
        alias="CORS_ALLOW_HEADERS",
    )

    # ------------------------------------------------------------------
    # Streaming / orchestrator behavior
    # ------------------------------------------------------------------
    # ENABLE_STREAM controls whether the proxy attempts SSE streaming when
    # the client asks for it (via Accept: text/event-stream).
    ENABLE_STREAM: bool = Field(
        default=True,
        alias="ENABLE_STREAM",
    )

    # CHAIN_WAIT_MODE controls how chained calls behave when you extend
    # P4Orchestrator (e.g. "sequential" vs "parallel" in future).
    CHAIN_WAIT_MODE: str = Field(
        default="sequential",
        alias="CHAIN_WAIT_MODE",
    )

    # ------------------------------------------------------------------
    # Timeouts (seconds)
    # ------------------------------------------------------------------
    # RELAY_TIMEOUT: end‑to‑end timeout for a request through the relay.
    RELAY_TIMEOUT: float = Field(
        default=120.0,
        alias="RELAY_TIMEOUT",
    )

    # PROXY_TIMEOUT: timeout used for the upstream OpenAI HTTP request.
    PROXY_TIMEOUT: float = Field(
        default=120.0,
        alias="PROXY_TIMEOUT",
    )

    # ------------------------------------------------------------------
    # Schemas / tools
    # ------------------------------------------------------------------
    TOOLS_MANIFEST: str = Field(
        default="app/manifests/tools_manifest.json",
        alias="TOOLS_MANIFEST",
    )

    # Path to your validation / API-reference schema. This is wired to
    # VALIDATION_SCHEMA_PATH in `.env` and points at your PDF ground truth
    # (e.g. ChatGPT-API_reference_ground_truth-2025-10-29.pdf).
    VALIDATION_SCHEMA_PATH: Optional[str] = Field(
        default=None,
        alias="VALIDATION_SCHEMA_PATH",
    )

    # ------------------------------------------------------------------
    # Meta
    # ------------------------------------------------------------------
    PYTHON_VERSION: str = Field(
        default=platform.python_version(),
        alias="PYTHON_VERSION",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """
    Singleton settings loader.
    """
    return Settings()


settings = get_settings()
