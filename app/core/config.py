# app/core/config.py

from __future__ import annotations

import logging
from functools import lru_cache
from typing import List

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger("relay")


class Settings(BaseSettings):
    """
    Centralised application configuration.

    All values may be overridden via environment variables as indicated by `alias`.
    """

    # -------- OpenAI core configuration --------
    OPENAI_API_KEY: str = Field(default="", alias="OPENAI_API_KEY")
    OPENAI_API_BASE: AnyHttpUrl = Field(
        default="https://api.openai.com/v1",
        alias="OPENAI_API_BASE",
    )

    # Assistants & Realtime beta headers (used by tests and forwarder)
    OPENAI_ASSISTANTS_BETA: str = Field(
        default="assistants=v2",
        alias="OPENAI_ASSISTANTS_BETA",
    )
    OPENAI_REALTIME_BETA: str = Field(
        default="realtime=v1",
        alias="OPENAI_REALTIME_BETA",
    )

    # Default models (aligned with your Render configuration)
    DEFAULT_MODEL: str = Field(
        default="gpt-5.1",  # updated per your env
        alias="DEFAULT_MODEL",
    )
    REALTIME_MODEL: str = Field(
        default="gpt-4o-realtime-preview",  # updated per your env
        alias="REALTIME_MODEL",
    )

    # -------- Relay identity / runtime --------
    RELAY_AUTH_ENABLED: bool = Field(
        default=True,
        alias="RELAY_AUTH_ENABLED",
    )
    RELAY_HOST: str = Field(default="0.0.0.0", alias="RELAY_HOST")
    RELAY_PORT: int = Field(default=8000, alias="RELAY_PORT")
    RELAY_NAME: str = Field(
        default="ChatGPT Team Relay",
        alias="RELAY_NAME",
    )
    RELAY_TIMEOUT: int = Field(default=120, alias="RELAY_TIMEOUT")
    PROXY_TIMEOUT: int = Field(default=120, alias="PROXY_TIMEOUT")
    PYTHON_VERSION: str = Field(default="3.12.5", alias="PYTHON_VERSION")

    # -------- Auth / secrets for relay usage --------
    RELAY_KEY: str = Field(default="", alias="RELAY_KEY")
    CHATGPT_ACTIONS_SECRET: str = Field(
        default="",
        alias="CHATGPT_ACTIONS_SECRET",
    )
    OPENAI_WEBHOOK_SECRET: str = Field(
        default="",
        alias="OPENAI_WEBHOOK_SECRET",
    )

    # -------- CORS config --------
    # Keep as plain strings so env can stay:
    # "https://chat.openai.com,https://platform.openai.com"
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

    # -------- Tools & validation schema --------
    TOOLS_MANIFEST: str = Field(
        default="app/manifests/tools_manifest.json",
        alias="TOOLS_MANIFEST",
    )
    VALIDATION_SCHEMA_PATH: str = Field(
        # Used by SchemaValidationMiddleware if you wire it up
        default="ChatGPT-API_reference_ground_truth-2025-10-29.pdf",
        alias="VALIDATION_SCHEMA_PATH",
    )

    # -------- Logging --------
    LOG_LEVEL: str = Field(default="info", alias="LOG_LEVEL")
    LOG_FORMAT: str = Field(default="json", alias="LOG_FORMAT")
    LOG_COLOR: bool = Field(default=False, alias="LOG_COLOR")

    # -------- Feature flags / orchestration --------
    ENABLE_STREAM: bool = Field(default=True, alias="ENABLE_STREAM")
    # can be "sequential" / "parallel" in a more complex setup;
    # here we just keep it as a free string.
    CHAIN_WAIT_MODE: str = Field(default="sequential", alias="CHAIN_WAIT_MODE")

    # -------- pydantic-settings config --------
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # -------- Convenience helpers --------
    def cors_allow_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ALLOW_ORIGINS.split(",") if o.strip()]

    def cors_allow_methods_list(self) -> List[str]:
        return [m.strip() for m in self.CORS_ALLOW_METHODS.split(",") if m.strip()]

    def cors_allow_headers_list(self) -> List[str]:
        return [h.strip() for h in self.CORS_ALLOW_HEADERS.split(",") if h.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings: Settings = get_settings()
