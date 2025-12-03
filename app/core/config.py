# app/core/config.py
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
    OPENAI_API_BASE: AnyHttpUrl = Field(
        default="https://api.openai.com",
        alias="OPENAI_API_BASE",
    )
    OPENAI_API_KEY: str = Field(
        default="",
        alias="OPENAI_API_KEY",
    )

    # Default models
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

    # Optional external hostname (used only for metadata / logging)
    RELAY_HOST: Optional[str] = Field(
        default=None,
        alias="RELAY_HOST",
    )

    # ------------------------------------------------------------------
    # Timeouts (seconds)
    # ------------------------------------------------------------------
    RELAY_TIMEOUT: float = Field(
        default=120.0,
        alias="RELAY_TIMEOUT",
    )
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

    JSON_SCHEMA_PATH: Optional[str] = Field(
        default=None,
        alias="JSON_SCHEMA_PATH",
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
