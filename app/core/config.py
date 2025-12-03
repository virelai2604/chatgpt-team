from __future__ import annotations

from functools import lru_cache
from typing import Optional

import sys
from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central configuration for the ChatGPT Team Relay.

    All values are loaded from environment variables or `.env`.
    Compatible with pydantic v2 + pydantic-settings v2.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ------------------------------------------------------------------
    # Core relay / app mode
    # ------------------------------------------------------------------
    ENVIRONMENT: str = Field(default="development", alias="ENVIRONMENT")
    APP_MODE: str = Field(default="development", alias="APP_MODE")

    # ------------------------------------------------------------------
    # OpenAI upstream config
    # ------------------------------------------------------------------
    OPENAI_API_BASE: AnyHttpUrl = Field(
        default="https://api.openai.com", alias="OPENAI_API_BASE"
    )
    OPENAI_API_KEY: str = Field(default="", alias="OPENAI_API_KEY")

    # Default chat / reasoning model used when callers don't override.
    DEFAULT_MODEL: str = Field(default="gpt-5.1", alias="DEFAULT_MODEL")

    # Default realtime model for websocket / session helpers.
    REALTIME_MODEL: str = Field(
        default="gpt-4o-realtime-preview",
        alias="REALTIME_MODEL",
    )

    # Assistants / Realtime beta headers – match render.yaml env:
    #   OPENAI_ASSISTANTS_BETA = "assistants=v2"
    #   OPENAI_REALTIME_BETA   = "realtime=v1"
    OPENAI_ASSISTANTS_BETA: str = Field(
        default="assistants=v2", alias="OPENAI_ASSISTANTS_BETA"
    )
    OPENAI_REALTIME_BETA: str = Field(
        default="realtime=v1", alias="OPENAI_REALTIME_BETA"
    )

    # ------------------------------------------------------------------
    # Relay identity / host
    # ------------------------------------------------------------------
    RELAY_NAME: str = Field(
        default="ChatGPT Team Relay",
        alias="RELAY_NAME",
    )
    RELAY_HOST: str = Field(
        default="http://localhost:8000",
        alias="RELAY_HOST",
    )

    # Network timeouts (seconds)
    RELAY_TIMEOUT: float = Field(default=30.0, alias="RELAY_TIMEOUT")
    PROXY_TIMEOUT: float = Field(default=120.0, alias="PROXY_TIMEOUT")

    # ------------------------------------------------------------------
    # Relay auth (for /v1/* and /relay/*)
    # ------------------------------------------------------------------
    RELAY_AUTH_ENABLED: bool = Field(
        default=True,
        alias="RELAY_AUTH_ENABLED",
    )
    RELAY_KEY: str = Field(
        default="",
        alias="RELAY_KEY",
    )

    # ------------------------------------------------------------------
    # Tools manifest & logging
    # ------------------------------------------------------------------
    TOOLS_MANIFEST: str = Field(
        default="tools_manifest.json",
        alias="TOOLS_MANIFEST",
    )

    LOG_LEVEL: str = Field(default="info", alias="LOG_LEVEL")
    LOG_FORMAT: str = Field(default="text", alias="LOG_FORMAT")
    LOG_COLOR: bool = Field(default=False, alias="LOG_COLOR")

    # ------------------------------------------------------------------
    # Misc / meta
    # ------------------------------------------------------------------
    PYTHON_VERSION: str = Field(
        default=sys.version.split(" ")[0],
        alias="PYTHON_VERSION",
    )


@lru_cache()
def get_settings() -> Settings:
    """
    Cached Settings instance.

    Usage:
        from app.core.config import settings
    """
    return Settings()  # type: ignore[misc]


# Singleton-like settings object for convenient import
settings: Settings = get_settings()
