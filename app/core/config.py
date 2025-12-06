# app/core/config.py
from __future__ import annotations

import os
import platform
from dataclasses import dataclass
from functools import lru_cache
from typing import Optional


def _get_env(key: str, default: Optional[str] = None, *, required: bool = False) -> Optional[str]:
    """
    Read an environment variable with optional 'required' enforcement.

    We centralise this so tests and runtime both fail fast with a clear error
    if a required variable is missing.
    """
    value = os.getenv(key, default)
    if required and not value:
        raise RuntimeError(f"Environment variable {key} is required but not set")
    return value


@dataclass
class Settings:
    # Basic app identity
    project_name: str
    environment: str

    # OpenAI client configuration
    openai_api_key: str
    openai_base_url: str
    openai_organization: Optional[str]
    timeout_seconds: float
    max_retries: int
    log_level: str

    # Relay auth / tools wiring
    relay_auth_token: Optional[str]
    relay_auth_enabled: bool
    relay_key: Optional[str]
    tools_manifest: Optional[str]
    validation_schema_path: Optional[str]

    # Health / status metadata
    relay_name: str
    app_mode: str
    default_model: str
    realtime_model: str
    openai_api_base: str
    openai_assistants_beta: bool
    openai_realtime_beta: bool
    python_version: str


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Lazily construct a single Settings instance backed by environment variables.
    This is the canonical source of configuration for the relay.
    """
    project_name = _get_env("PROJECT_NAME", "chatgpt-team-relay") or "chatgpt-team-relay"
    environment = _get_env("ENVIRONMENT", "development") or "development"

    openai_base_url = _get_env("OPENAI_BASE_URL", "https://api.openai.com/v1") or "https://api.openai.com/v1"
    # This one is deliberately required – you must set it in your shell / .env.
    openai_api_key = _get_env("OPENAI_API_KEY", required=True) or ""
    openai_organization = _get_env("OPENAI_ORG_ID")

    timeout_seconds = float(_get_env("OPENAI_TIMEOUT_SECONDS", "20.0") or "20.0")
    max_retries = int(_get_env("OPENAI_MAX_RETRIES", "2") or "2")
    log_level = _get_env("LOG_LEVEL", "INFO") or "INFO"

    relay_auth_token = _get_env("RELAY_AUTH_TOKEN")
    relay_auth_enabled = (_get_env("RELAY_AUTH_ENABLED", "false") or "false").lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    relay_key = _get_env("RELAY_KEY")
    tools_manifest = _get_env("TOOLS_MANIFEST")
    validation_schema_path = _get_env("VALIDATION_SCHEMA_PATH")

    relay_name = _get_env("RELAY_NAME", project_name) or project_name
    app_mode = _get_env("APP_MODE", "relay") or "relay"
    default_model = _get_env("DEFAULT_MODEL", "gpt-4.1-mini") or "gpt-4.1-mini"
    realtime_model = _get_env("REALTIME_MODEL", "gpt-4o-realtime-preview") or "gpt-4o-realtime-preview"

    # For health reporting we keep api_base separate even though it's the same as base_url.
    openai_api_base = openai_base_url
    openai_assistants_beta = (_get_env("OPENAI_ASSISTANTS_BETA", "false") or "false").lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    openai_realtime_beta = (_get_env("OPENAI_REALTIME_BETA", "false") or "false").lower() in {
        "1",
        "true",
        "yes",
        "on",
    }

    python_version = _get_env("PYTHON_VERSION", platform.python_version()) or platform.python_version()

    settings = Settings(
        project_name=project_name,
        environment=environment,
        openai_api_key=openai_api_key,
        openai_base_url=openai_base_url,
        openai_organization=openai_organization,
        timeout_seconds=timeout_seconds,
        max_retries=max_retries,
        log_level=log_level,
        relay_auth_token=relay_auth_token,
        relay_auth_enabled=relay_auth_enabled,
        relay_key=relay_key,
        tools_manifest=tools_manifest,
        validation_schema_path=validation_schema_path,
        relay_name=relay_name,
        app_mode=app_mode,
        default_model=default_model,
        realtime_model=realtime_model,
        openai_api_base=openai_api_base,
        openai_assistants_beta=openai_assistants_beta,
        openai_realtime_beta=openai_realtime_beta,
        python_version=python_version,
    )

    # Backwards‑compatible uppercase aliases (e.g. settings.RELAY_NAME)
    for attr in (
        "project_name",
        "environment",
        "openai_api_key",
        "openai_base_url",
        "openai_organization",
        "timeout_seconds",
        "max_retries",
        "log_level",
        "relay_auth_token",
        "relay_auth_enabled",
        "relay_key",
        "tools_manifest",
        "validation_schema_path",
        "relay_name",
        "app_mode",
        "default_model",
        "realtime_model",
        "openai_api_base",
        "openai_assistants_beta",
        "openai_realtime_beta",
        "python_version",
    ):
        setattr(settings, attr.upper(), getattr(settings, attr))

    return settings


# Eagerly expose a module‑level singleton for legacy imports:
#   from app.core.config import settings
settings: Settings = get_settings()
