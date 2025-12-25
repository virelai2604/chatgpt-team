from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Optional

from app.utils.logger import get_logger

logger = get_logger(__name__)


def _env_bool(name: str, default: bool = False) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "y", "on"}


def _env_int(name: str, default: int) -> int:
    val = os.getenv(name)
    if val is None or not val.strip():
        return default
    try:
        return int(val)
    except ValueError:
        return default


@dataclass(frozen=True, slots=True)
class Settings:
    """
    Centralized settings for the relay.

    NOTE:
    - Use OPENAI_API_BASE to override upstream base (e.g. https://api.openai.com or https://api.openai.com/v1).
    - Relay auth is controlled by RELAY_AUTH_ENABLED and RELAY_AUTH_KEY.
    """

    # App / Environment
    APP_ENVIRONMENT: str = os.getenv("APP_ENVIRONMENT", "local")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # Relay auth (client -> relay)
    RELAY_AUTH_ENABLED: bool = _env_bool("RELAY_AUTH_ENABLED", True)
    RELAY_AUTH_KEY: str = os.getenv("RELAY_AUTH_KEY", "dev-relay-key")

    # Upstream OpenAI API
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_API_BASE: str = os.getenv("OPENAI_API_BASE", "https://api.openai.com")
    OPENAI_PROJECT: Optional[str] = os.getenv("OPENAI_PROJECT") or None
    OPENAI_ORG: Optional[str] = os.getenv("OPENAI_ORG") or None

    # HTTP client
    OPENAI_HTTP_TIMEOUT_S: int = _env_int("OPENAI_HTTP_TIMEOUT_S", 60)

    # Misc relay behavior
    DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "gpt-4o-mini")
    STRICT_UPSTREAM_PATHS: bool = _env_bool("STRICT_UPSTREAM_PATHS", False)

    # ---- Compatibility helpers ----

    @property
    def openai_api_key(self) -> str:
        return self.OPENAI_API_KEY

    @property
    def openai_base_url(self) -> str:
        # Kept intentionally flexible: may be "https://api.openai.com" or ".../v1".
        return self.OPENAI_API_BASE

    @property
    def openai_timeout_s(self) -> int:
        return self.OPENAI_HTTP_TIMEOUT_S

    # Compatibility aliases used by some route/meta code
    @property
    def OPENAI_BASE_URL(self) -> str:
        return self.openai_base_url

    @property
    def UPSTREAM_BASE_URL(self) -> str:
        return self.openai_base_url

    @property
    def upstream_base_url(self) -> str:
        return self.openai_base_url


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    s = Settings()
    if not s.OPENAI_API_KEY:
        logger.warning("OPENAI_API_KEY is not set. Upstream calls will fail.")
    return s


# Convenience singleton (OK for read-only usage)
settings = get_settings()
