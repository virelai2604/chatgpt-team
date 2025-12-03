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
    ENVIRONMENT: str = Field(
        default="local",
        alias="ENVIRONMENT",
        description="High-level deployment environment (local, staging, production, etc.).",
    )

    APP_MODE: str = Field(
        default="development",
        alias="APP_MODE",
        description="Application mode (development, test, production) for feature flags/logging.",
    )

    # ------------------------------------------------------------------
    # OpenAI upstream config
    # ------------------------------------------------------------------
    OPENAI_API_BASE: AnyHttpUrl = Field(
        default="https://api.openai.com",
        alias="OPENAI_API_BASE",
        description="Base URL for the OpenAI API.",
    )

    OPENAI_API_KEY: str = Field(
        default="",
        alias="OPENAI_API_KEY",
        description="Primary OpenAI API key used by the relay.",
    )

    # Default models
    DEFAULT_MODEL: str = Field(
        default="gpt-5.1",
        alias="DEFAULT_MODEL",
        description="Default text/reasoning model for generic requests.",
    )

    REALTIME_MODEL: str = Field(
        default="gpt-4o-realtime-preview",
        alias="REALTIME_MODEL",
        description="Default model for realtime (WebRTC/WebSocket) interactions.",
    )

    # Beta headers
    OPENAI_ASSISTANTS_BETA: str = Field(
        default="assistants=v2",
        alias="OPENAI_ASSISTANTS_BETA",
        description="OpenAI beta header toggle for Assistants v2.",
    )

    OPENAI_REALTIME_BETA: str = Field(
        default="realtime=v1",
        alias="OPENAI_REALTIME_BETA",
        description="OpenAI beta header toggle for Realtime API.",
    )

    # ------------------------------------------------------------------
    # Relay identity / auth
    # ------------------------------------------------------------------
    RELAY_NAME: str = Field(
        default="ChatGPT Team Relay",
        alias="RELAY_NAME",
        description="Human-readable name for this relay instance.",
    )

    RELAY_AUTH_ENABLED: bool = Field(
        default=False,
        alias="RELAY_AUTH_ENABLED",
        description="If True, enforce relay-level auth using RELAY_KEY.",
    )

    RELAY_KEY: Optional[str] = Field(
        default=None,
        alias="RELAY_KEY",
        description="Shared secret for relay authentication (if enabled).",
    )

    # Optional external hostname (used only for metadata / logging)
    RELAY_HOST: Optional[str] = Field(
        default=None,
        alias="RELAY_HOST",
        description="Optional public hostname / base URL of this relay.",
    )

    # ------------------------------------------------------------------
    # Timeouts (seconds)
    # ------------------------------------------------------------------
    RELAY_TIMEOUT: float = Field(
        default=120.0,
        alias="RELAY_TIMEOUT",
        description="Global timeout for relay-level operations (seconds).",
    )

    PROXY_TIMEOUT: float = Field(
        default=120.0,
        alias="PROXY_TIMEOUT",
        description="Timeout applied when proxying upstream calls to OpenAI (seconds).",
    )

    # ------------------------------------------------------------------
    # Schemas / tools
    # ------------------------------------------------------------------
    TOOLS_MANIFEST: str = Field(
        default="app/manifests/tools_manifest.json",
        alias="TOOLS_MANIFEST",
        description="Path to the tools manifest JSON used for tools/agents.",
    )

    JSON_SCHEMA_PATH: Optional[str] = Field(
        default=None,
        alias="JSON_SCHEMA_PATH",
        description="Optional path to additional JSON schemas for validation.",
    )

    # ------------------------------------------------------------------
    # CORS configuration
    # ------------------------------------------------------------------
    CORS_ALLOW_ORIGINS: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000",
        alias="CORS_ALLOW_ORIGINS",
        description=(
            "Comma-separated list of allowed origins for CORS. "
            "Used by app/main.py to configure CORSMiddleware."
        ),
    )

    CORS_ALLOW_METHODS: str = Field(
        default="GET,POST,PUT,PATCH,DELETE,OPTIONS",
        alias="CORS_ALLOW_METHODS",
        description=(
            "Comma-separated list of allowed HTTP methods for CORS. "
            "Defaults to common REST methods plus OPTIONS for preflight."
        ),
    )

    CORS_ALLOW_HEADERS: str = Field(
        default="Authorization,Content-Type,Accept,Origin,User-Agent,Cache-Control,Pragma",
        alias="CORS_ALLOW_HEADERS",
        description=(
            "Comma-separated list of allowed HTTP headers for CORS. "
            "Include Authorization and Content-Type so browsers and clients work correctly."
        ),
    )

    # ------------------------------------------------------------------
    # Meta
    # ------------------------------------------------------------------
    PYTHON_VERSION: str = Field(
        default=platform.python_version(),
        alias="PYTHON_VERSION",
        description="Python version this app is running on (captured at import time).",
    )

    # ------------------------------------------------------------------
    # Pydantic configuration
    # ------------------------------------------------------------------
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """
    Singleton settings loader to avoid repeatedly parsing environment variables.
    """
    return Settings()


# Eagerly instantiate settings at import time for convenience
settings = get_settings()
