from __future__ import annotations

from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central configuration for the relay.

    IMPORTANT:
    - OPENAI_API_BASE is the upstream OpenAI API base for the relay to call.
    - OPENAI_BASE_URL is commonly used by *clients* (SDK) to point at a proxy/relay.
      The relay should NOT use OPENAI_BASE_URL for upstream to avoid self-calls.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- App ---
    APP_MODE: str = Field(default="development")
    ENVIRONMENT: str = Field(default="local")

    # --- Relay Auth ---
    RELAY_AUTH_ENABLED: bool = Field(default=False)
    RELAY_KEY: str = Field(default="")
    # Header clients send when not using Authorization: Bearer ...
    RELAY_AUTH_HEADER: str = Field(default="x-relay-key")

    # --- OpenAI Upstream ---
    OPENAI_API_KEY: str = Field(default="")
    # Upstream base used by the relay for forwarding.
    OPENAI_API_BASE: str = Field(default="https://api.openai.com/v1")
    OPENAI_ORG: Optional[str] = Field(default=None)
    OPENAI_PROJECT: Optional[str] = Field(default=None)

    # --- Timeouts / Defaults ---
    PROXY_TIMEOUT_SECONDS: float = Field(default=90.0)
    DEFAULT_MODEL: str = Field(default="gpt-5.1")

    # ---- Compatibility aliases (code may reference lowercase attrs) ----
    @property
    def openai_api_key(self) -> str:
        return self.OPENAI_API_KEY

    @property
    def openai_api_base(self) -> str:
        return self.OPENAI_API_BASE

    @property
    def openai_base_url(self) -> str:
        # Alias used by some modules; keep equal to OPENAI_API_BASE.
        return self.OPENAI_API_BASE

    @property
    def relay_auth_enabled(self) -> bool:
        return self.RELAY_AUTH_ENABLED

    @property
    def relay_key(self) -> str:
        return self.RELAY_KEY

    @property
    def relay_auth_header(self) -> str:
        return self.RELAY_AUTH_HEADER

    @property
    def proxy_timeout_seconds(self) -> float:
        return self.PROXY_TIMEOUT_SECONDS


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
