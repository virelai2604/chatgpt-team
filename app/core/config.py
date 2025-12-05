# app/core/config.py

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Optional


@dataclass(frozen=True)
class Settings:
    """
    Central configuration for the ChatGPT Team Relay.

    This is intentionally simple and environment-driven (12‑factor style).
    """

    project_name: str
    environment: str

    # OpenAI core configuration
    openai_api_key: str
    openai_base_url: str
    openai_organization: Optional[str]

    # HTTP client behaviour
    timeout_seconds: float
    max_retries: int

    # Logging
    log_level: str

    # Relay auth / tools manifest
    RELAY_KEY: Optional[str]
    RELAY_AUTH_ENABLED: bool
    TOOLS_MANIFEST: str

    @property
    def debug(self) -> bool:
        return self.environment.lower() != "production"


def _get_env(key: str, default: Optional[str] = None, *, required: bool = False) -> Optional[str]:
    value = os.getenv(key, default)
    if required and (value is None or value == ""):
        raise RuntimeError(f"Environment variable {key} is required but not set")
    return value


def _bool_env(key: str, default: bool = False) -> bool:
    raw = os.getenv(key)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Load and cache configuration from environment.

    This is safe to call from anywhere and keeps a single Settings instance
    for the process lifetime.
    """
    project_name = _get_env("PROJECT_NAME", "chatgpt-team-relay") or "chatgpt-team-relay"
    environment = _get_env("ENVIRONMENT", _get_env("APP_ENV", "development")) or "development"

    openai_api_key = _get_env("OPENAI_API_KEY", required=True)  # type: ignore[assignment]
    openai_base_url = _get_env("OPENAI_API_BASE", "https://api.openai.com/v1") or "https://api.openai.com/v1"
    openai_organization = _get_env("OPENAI_ORGANIZATION")

    timeout_seconds = float(_get_env("OPENAI_TIMEOUT_SECONDS", "20.0") or "20.0")
    max_retries = int(_get_env("OPENAI_MAX_RETRIES", "2") or "2")

    log_level = _get_env("LOG_LEVEL", "INFO") or "INFO"

    relay_key = _get_env("RELAY_KEY")
    relay_auth_enabled = _bool_env("RELAY_AUTH_ENABLED", default=bool(relay_key))

    tools_manifest = _get_env(
        "TOOLS_MANIFEST",
        "app/manifests/tools_manifest.json",
    ) or "app/manifests/tools_manifest.json"

    return Settings(
        project_name=project_name,
        environment=environment,
        openai_api_key=openai_api_key,
        openai_base_url=openai_base_url,
        openai_organization=openai_organization,
        timeout_seconds=timeout_seconds,
        max_retries=max_retries,
        log_level=log_level,
        RELAY_KEY=relay_key,
        RELAY_AUTH_ENABLED=relay_auth_enabled,
        TOOLS_MANIFEST=tools_manifest,
    )


# Backwards‑compatible module‑level settings object
settings: Settings = get_settings()
