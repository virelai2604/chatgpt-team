from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Optional


def _env_str(name: str, default: str = "") -> str:
    v = os.getenv(name)
    return default if v is None else str(v)


def _env_int(name: str, default: int) -> int:
    v = os.getenv(name)
    if v is None or v == "":
        return int(default)
    try:
        return int(v)
    except ValueError:
        return int(default)


def _env_float(name: str, default: float) -> float:
    v = os.getenv(name)
    if v is None or v == "":
        return float(default)
    try:
        return float(v)
    except ValueError:
        return float(default)


def _env_bool(name: str, default: bool) -> bool:
    v = os.getenv(name)
    if v is None or v == "":
        return bool(default)
    return str(v).strip().lower() in ("1", "true", "t", "yes", "y", "on")


@dataclass
class Settings:
    # App identity
    RELAY_NAME: str
    APP_MODE: str
    ENVIRONMENT: str

    # Relay auth
    RELAY_AUTH_ENABLED: bool
    RELAY_KEY: str

    # OpenAI upstream
    OPENAI_API_KEY: str
    OPENAI_API_BASE: str
    OPENAI_ORG: str
    OPENAI_PROJECT: str

    # Timeouts
    PROXY_TIMEOUT_SECONDS: float

    # Logging / tracing
    LOG_LEVEL: str

    # --- Back-compat aliases (older snapshots referenced these names) ---
    @property
    def openai_api_key(self) -> str:
        return self.OPENAI_API_KEY

    @property
    def openai_api_base(self) -> str:
        return self.OPENAI_API_BASE

    @property
    def openai_base_url(self) -> str:
        # Back-compat: some modules expect `settings.openai_base_url`.
        # This should point at the upstream OpenAI API base.
        return self.OPENAI_API_BASE

    @property
    def relay_auth_enabled(self) -> bool:
        return self.RELAY_AUTH_ENABLED

    @property
    def relay_key(self) -> str:
        return self.RELAY_KEY


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        RELAY_NAME=_env_str("RELAY_NAME", "chatgpt-team-relay"),
        APP_MODE=_env_str("APP_MODE", "relay"),
        ENVIRONMENT=_env_str("ENVIRONMENT", "local"),

        # IMPORTANT: default False so local tests can call /, /health, /openapi.json without auth.
        RELAY_AUTH_ENABLED=_env_bool("RELAY_AUTH_ENABLED", False),
        RELAY_KEY=_env_str("RELAY_KEY", "dev-relay-key"),

        OPENAI_API_KEY=_env_str("OPENAI_API_KEY", ""),
        # IMPORTANT: do NOT default to OPENAI_BASE_URL (client-side proxy var).
        OPENAI_API_BASE=_env_str("OPENAI_API_BASE", "https://api.openai.com/v1"),
        OPENAI_ORG=_env_str("OPENAI_ORG", ""),
        OPENAI_PROJECT=_env_str("OPENAI_PROJECT", ""),

        PROXY_TIMEOUT_SECONDS=_env_float("PROXY_TIMEOUT_SECONDS", 90.0),

        LOG_LEVEL=_env_str("LOG_LEVEL", "INFO"),
    )


# Module-level singleton used throughout the app
settings = get_settings()
