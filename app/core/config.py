# app/core/config.py

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Optional


@dataclass(frozen=True)
class Settings:
    """
    Single source of truth for relay configuration.

    Backed by environment variables, but kept as a simple dataclass so the
    rest of the codebase stays framework-agnostic and fast to import.
    """

    # Project / environment
    project_name: str
    environment: str  # e.g. "development", "staging", "production"

    # OpenAI API
    openai_api_key: str
    openai_base_url: str
    openai_organization: Optional[str]
    timeout_seconds: float
    max_retries: int
    log_level: str

    # Relay auth
    relay_key: Optional[str]
    relay_auth_enabled: bool

    # Tools / validation
    tools_manifest: str
    validation_schema_path: Optional[str]


def _get_env(name: str, default: Optional[str] = None, *, required: bool = False) -> str:
    value = os.getenv(name, default)
    if required and not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _bool_env(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.lower() in {"1", "true", "yes", "on"}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Load settings once from environment. All other modules should import this
    function (or the module-level `settings`) instead of reading os.environ
    directly.
    """
    project_name = _get_env("PROJECT_NAME", "ChatGPT Team Relay")
    environment = _get_env("ENVIRONMENT", "development")

    openai_api_key = _get_env("OPENAI_API_KEY", required=True)
    openai_base_url = _get_env("OPENAI_BASE_URL", "https://api.openai.com/v1")

    openai_org = (
        os.getenv("OPENAI_ORG_ID")
        or os.getenv("OPENAI_ORGANIZATION")
        or os.getenv("OPENAI_ORG")
    )

    timeout_seconds = float(_get_env("OPENAI_TIMEOUT_SECONDS", "20.0"))
    max_retries = int(_get_env("OPENAI_MAX_RETRIES", "2"))
    log_level = _get_env("LOG_LEVEL", "INFO")

    relay_key = os.getenv("RELAY_KEY")
    relay_auth_enabled = _bool_env("RELAY_AUTH_ENABLED", default=bool(relay_key))

    tools_manifest = _get_env(
        "TOOLS_MANIFEST", "app/manifests/tools_manifest.json"
    )
    validation_schema_path = os.getenv("VALIDATION_SCHEMA_PATH")

    return Settings(
        project_name=project_name,
        environment=environment,
        openai_api_key=openai_api_key,
        openai_base_url=openai_base_url,
        openai_organization=openai_org,
        timeout_seconds=timeout_seconds,
        max_retries=max_retries,
        log_level=log_level,
        relay_key=relay_key,
        relay_auth_enabled=relay_auth_enabled,
        tools_manifest=tools_manifest,
        validation_schema_path=validation_schema_path,
    )


# Convenient singleton for modules that just need readonly configuration.
settings: Settings = get_settings()
