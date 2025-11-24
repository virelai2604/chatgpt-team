from __future__ import annotations

import os

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central configuration for the ChatGPT Team Relay (P4 Codex).

    - Compatible with Pydantic v2 via pydantic-settings.
    - Maps directly to environment variables used in your Render service.
    """

    # ------------------------------------------------------------------
    # Identity & mode
    # ------------------------------------------------------------------
    RELAY_NAME: str = Field(default="ChatGPT Team Relay (P4 Codex)")
    APP_MODE: str = Field(default="production")      # development | production | test
    ENVIRONMENT: str = Field(default="production")   # surfaced in /v1/health

    # ------------------------------------------------------------------
    # OpenAI upstream
    # ------------------------------------------------------------------
    OPENAI_API_BASE: str = Field(
        default="https://api.openai.com"
    )
    OPENAI_API_KEY: str = Field(
        default="",  # override via env in Render
    )
    DEFAULT_MODEL: str = Field(
        default="gpt-4o-mini"
    )
    OPENAI_ASSISTANTS_BETA: str = Field(
        default="assistants=v2"
    )
    OPENAI_REALTIME_BETA: str = Field(
        default="realtime=v1"
    )

    # ------------------------------------------------------------------
    # Relay behavior & timeouts
    # ------------------------------------------------------------------
    ENABLE_STREAM: bool = Field(default=True)
    CHAIN_WAIT_MODE: str = Field(default="sequential")  # or "concurrent"

    PROXY_TIMEOUT: int = Field(default=30)   # seconds
    RELAY_TIMEOUT: int = Field(default=120)  # seconds

    # ------------------------------------------------------------------
    # Tools & validation
    # ------------------------------------------------------------------
    TOOLS_MANIFEST: str = Field(
        default="app/manifests/tools_manifest.json"
    )
    VALIDATION_SCHEMA_PATH: str = Field(
        default="ChatGPT-API_reference_ground_truth-2025-10-29.pdf"
    )

    # ------------------------------------------------------------------
    # CORS
    # ------------------------------------------------------------------
    CORS_ALLOW_ORIGINS: str = Field(default="*")
    CORS_ALLOW_METHODS: str = Field(
        default="GET,POST,PUT,PATCH,DELETE,OPTIONS"
    )
    CORS_ALLOW_HEADERS: str = Field(
        default="Authorization,Content-Type,Accept"
    )

    # ------------------------------------------------------------------
    # Realtime defaults
    # ------------------------------------------------------------------
    REALTIME_MODEL: str = Field(
        default="gpt-4.1-mini"
    )

    # ------------------------------------------------------------------
    # Pydantic v2 settings config
    # ------------------------------------------------------------------
    model_config = SettingsConfigDict(
        env_file=os.getenv("ENV_FILE", ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


# Singleton instance imported across the app:
settings = Settings()
