# app/core/config.py
from dataclasses import dataclass
from functools import lru_cache
import os
from typing import Optional


@dataclass(frozen=True)
class Settings:
    # General
    project_name: str
    environment: str

    # OpenAI
    openai_api_key: Optional[str]
    openai_base_url: str
    openai_organization: Optional[str]

    # HTTP / client behavior
    timeout_seconds: float
    max_retries: int
    log_level: str

    # Relay auth
    relay_auth_token: Optional[str]

    @property
    def debug(self) -> bool:
        """
        Convenience flag: anything except 'production' is treated as debug.
        """
        return self.environment.lower() != "production"


def _get_env(name: str, default: Optional[str] = None) -> Optional[str]:
    """
    Read an environment variable, returning default if unset/empty.
    No validation is done here; callers can coerce types.
    """
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return value


def _get_env_float(name: str, default: float) -> float:
    raw = _get_env(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _get_env_int(name: str, default: int) -> int:
    raw = _get_env(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


@lru_cache
def get_settings() -> Settings:
    """
    Canonical Settings factory.
    Cached so config is computed once per process.
    """
    return Settings(
        project_name=_get_env("PROJECT_NAME", "chatgpt-team-relay") or "chatgpt-team-relay",
        environment=_get_env("ENVIRONMENT", "development") or "development",
        openai_api_key=_get_env("OPENAI_API_KEY"),  # validated later in http_client
        openai_base_url=_get_env("OPENAI_BASE_URL", "https://api.openai.com/v1") or "https://api.openai.com/v1",
        openai_organization=_get_env("OPENAI_ORG_ID"),
        timeout_seconds=_get_env_float("OPENAI_TIMEOUT_SECONDS", 20.0),
        max_retries=_get_env_int("OPENAI_MAX_RETRIES", 2),
        log_level=_get_env("LOG_LEVEL", "INFO") or "INFO",
        relay_auth_token=_get_env("RELAY_AUTH_TOKEN"),
    )


# Module-level alias for legacy imports:
# Many modules do: `from app.core.config import settings`
settings: Settings = get_settings()
