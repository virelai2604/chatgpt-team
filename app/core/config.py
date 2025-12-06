# app/core/config.py
from dataclasses import dataclass
from functools import lru_cache
import os
from typing import Optional


@dataclass(frozen=True)
class Settings:
    project_name: str
    environment: str

    openai_api_key: str
    openai_base_url: str
    openai_organization: Optional[str]

    timeout_seconds: float
    max_retries: int

    log_level: str
    relay_auth_token: Optional[str]

    @property
    def debug(self) -> bool:
        return self.environment.lower() != "production"


def _get_env(name: str, default: Optional[str] = None, required: bool = False) -> Optional[str]:
    value = os.getenv(name, default)
    if required and (value is None or value == ""):
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


@lru_cache
def get_settings() -> Settings:
    return Settings(
        project_name=_get_env("PROJECT_NAME", "chatgpt-team-relay") or "chatgpt-team-relay",
        environment=_get_env("ENVIRONMENT", "development") or "development",
        openai_api_key=_get_env("OPENAI_API_KEY", required=True) or "",
        openai_base_url=_get_env("OPENAI_BASE_URL", "https://api.openai.com/v1") or "https://api.openai.com/v1",
        openai_organization=_get_env("OPENAI_ORG_ID"),
        timeout_seconds=float(_get_env("OPENAI_TIMEOUT_SECONDS", "20.0") or "20.0"),
        max_retries=int(_get_env("OPENAI_MAX_RETRIES", "2") or "2"),
        log_level=_get_env("LOG_LEVEL", "INFO") or "INFO",
        relay_auth_token=_get_env("RELAY_AUTH_TOKEN"),
    )
