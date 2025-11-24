from __future__ import annotations

import os
from typing import Literal

from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    # Identity and mode
    RELAY_NAME: str = Field(default="ChatGPT Team Relay")
    APP_MODE: Literal["development", "production", "test"] = Field(
        default="development"
    )
    ENVIRONMENT: str = Field(default="local")

    # OpenAI upstream
    OPENAI_API_BASE: str = Field(default="https://api.openai.com")
    OPENAI_API_KEY: str = Field(default="")
    DEFAULT_MODEL: str = Field(default="gpt-4o-mini")
    OPENAI_ASSISTANTS_BETA: str = Field(default="assistants=v2")
    OPENAI_REALTIME_BETA: str = Field(default="realtime=v1")

    # Relay behavior
    ENABLE_STREAM: bool = Field(default=True)
    CHAIN_WAIT_MODE: str = Field(default="sequential")  # or "concurrent"
    PROXY_TIMEOUT: int = Field(default=30)
    RELAY_TIMEOUT: int = Field(default=120)

    # Tools & validation
    TOOLS_MANIFEST: str = Field(default="app/manifests/tools_manifest.json")
    VALIDATION_SCHEMA_PATH: str = Field(
        default="ChatGPT-API_reference_ground_truth-2025-10-29.pdf"
    )

    # CORS
    CORS_ALLOW_ORIGINS: str = Field(default="*")
    CORS_ALLOW_METHODS: str = Field(default="GET,POST,PUT,PATCH,DELETE,OPTIONS")
    CORS_ALLOW_HEADERS: str = Field(default="Authorization,Content-Type,Accept")

    class Config:
        # Load from environment by default (dotenv if you use python-dotenv)
        env_file = os.getenv("ENV_FILE", ".env")
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()
