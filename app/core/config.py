from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App / environment modes
    APP_MODE: str = Field(default="development")
    ENVIRONMENT: str = Field(default="development")

    # OpenAI upstream configuration
    OPENAI_API_BASE: str = Field(default="https://api.openai.com")
    OPENAI_API_KEY: str = Field(default="")
    OPENAI_ASSISTANTS_BETA: str = Field(default="assistants=v2")
    OPENAI_REALTIME_BETA: str = Field(default="realtime=v1")

    # Models
    DEFAULT_MODEL: str = Field(default="gpt-4o-mini")
    REALTIME_MODEL: str = Field(default="gpt-4.1-mini")

    # Behaviour flags / timeouts
    ENABLE_STREAM: bool = Field(default=True)
    CHAIN_WAIT_MODE: str = Field(default="sequential")
    PROXY_TIMEOUT: int = Field(default=120)
    RELAY_TIMEOUT: int = Field(default=120)

    # Relay identity
    RELAY_NAME: str = Field(default="ChatGPT Team Relay")

    # Tooling / validation
    TOOLS_MANIFEST: str = Field(default="app/manifests/tools_manifest.json")
    VALIDATION_SCHEMA_PATH: str = Field(
        default="ChatGPT-API_reference_ground_truth-2025-10-29.pdf"
    )

    # CORS
    CORS_ALLOW_ORIGINS: str = Field(default="*")
    CORS_ALLOW_METHODS: str = Field(
        default="GET,POST,PUT,PATCH,DELETE,OPTIONS"
    )
    CORS_ALLOW_HEADERS: str = Field(default="*")

    # Pydantic v2 settings config
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_allow_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ALLOW_ORIGINS.split(",") if o.strip()]

    @property
    def cors_allow_methods_list(self) -> List[str]:
        return [m.strip() for m in self.CORS_ALLOW_METHODS.split(",") if m.strip()]

    @property
    def cors_allow_headers_list(self) -> List[str]:
        return [h.strip() for h in self.CORS_ALLOW_HEADERS.split(",") if h.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
