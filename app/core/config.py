# app/core/config.py

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import os
from typing import Optional


def _get_env(name: str, default: Optional[str] = None, *, required: bool = False) -> str:
    """
    Read an environment variable with optional default and required flag.
    Raises RuntimeError if required and missing/empty.
    """
    value = os.getenv(name, default)
    if value is None or value == "":
        if required:
            raise RuntimeError(f"Missing required environment variable: {name}")
        return default or ""
    return value


def _bool_env(name: str, default: bool = False) -> bool:
    """
    Parse a boolean environment variable.
    Accepts: 1, true, yes, on (case-insensitive) as truthy.
    """
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    """
    Central configuration for the ChatGPT Team Relay.

    This is intentionally a simple dataclass so it can be used easily in tests
    and by FastAPI startup hooks.
    """

    # Application identity
    project_name: str
    environment: str

    # Upstream OpenAI configuration
    openai_api_key: str
    openai_base_url: str
    openai_organization: Optional[str]

    # HTTP behaviour for the OpenAI client
    timeout_seconds: float
    max_retries: int

    # Logging
    log_level: str  # <-- this is the attribute you should use

    # Relay auth / tools
    # These are uppercase on purpose so that callers can use settings.RELAY_KEY
    # as a clear signal these are env-style fields.
    RELAY_KEY: Optional[str]
    RELAY_AUTH_ENABLED: bool
    TOOLS_MANIFEST: str

    @property
    def debug(self) -> bool:
        return self.environment.lower() != "production"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Load and cache settings from environment variables.

    Required:
        OPENAI_API_KEY

    Optional (with defaults):
        PROJECT_NAME            (default: chatgpt-team-relay)
        ENVIRONMENT             (default: development)
        OPENAI_BASE_URL         (default: https://api.openai.com/v1)
        OPENAI_ORG_ID / OPENAI_ORG / OPENAI_ORGANIZATION
        OPENAI_TIMEOUT_SECONDS  (default: 20.0)
        OPENAI_MAX_RETRIES      (default: 2)
        LOG_LEVEL               (default: INFO)
        RELAY_KEY               (auth key for the relay)
        RELAY_AUTH_ENABLED      (default: True if RELAY_KEY set, else False)
        TOOLS_MANIFEST          (default: app/manifests/tools_manifest.json)
    """
    environment = _get_env("ENVIRONMENT", "development") or "development"

    openai_api_key = _get_env("OPENAI_API_KEY", required=True)
    openai_base_url = (
        _get_env("OPENAI_BASE_URL", "https://api.openai.com/v1")
        or "https://api.openai.com/v1"
    )

    # Accept multiple organisation env names for flexibility
    org = (
        os.getenv("OPENAI_ORG_ID")
        or os.getenv("OPENAI_ORG")
        or os.getenv("OPENAI_ORGANIZATION")
        or ""
    )

    timeout_seconds = float(_get_env("OPENAI_TIMEOUT_SECONDS", "20.0") or "20.0")
    max_retries = int(_get_env("OPENAI_MAX_RETRIES", "2") or "2")
    log_level = _get_env("LOG_LEVEL", "INFO") or "INFO"

    # Relay auth: prefer RELAY_KEY, then legacy RELAY_AUTH_TOKEN
    relay_key = _get_env("RELAY_KEY") or _get_env("RELAY_AUTH_TOKEN") or ""
    relay_auth_enabled = _bool_env(
        "RELAY_AUTH_ENABLED",
        default=bool(relay_key),
    )

    tools_manifest = (
        _get_env("TOOLS_MANIFEST", "app/manifests/tools_manifest.json")
        or "app/manifests/tools_manifest.json"
    )

    return Settings(
        project_name=_get_env("PROJECT_NAME", "chatgpt-team-relay")
        or "chatgpt-team-relay",
        environment=environment,
        openai_api_key=openai_api_key,
        openai_base_url=openai_base_url,
        openai_organization=org or None,
        timeout_seconds=timeout_seconds,
        max_retries=max_retries,
        log_level=log_level,
        RELAY_KEY=relay_key or None,
        RELAY_AUTH_ENABLED=relay_auth_enabled,
        TOOLS_MANIFEST=tools_manifest,
    )


# Convenience instance for modules that want `from app.core.config import settings`
settings: Settings = get_settings()
