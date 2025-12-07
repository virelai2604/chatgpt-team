# app/core/config.py
from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from typing import List, Optional


def _get_env(key: str, default: Optional[str] = None, *, required: bool = False) -> str:
    value = os.getenv(key, default)
    if required and (value is None or value == ""):
        raise RuntimeError(f"Environment variable {key} is required but not set")
    return value or ""


def _get_bool(key: str, default: bool = False) -> bool:
    value = os.getenv(key)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _get_int(key: str, default: int) -> int:
    value = os.getenv(key)
    if value is None or value == "":
        return default
    try:
        return int(value)
    except ValueError:
        raise RuntimeError(f"Environment variable {key} must be an integer, got {value!r}")


def _get_csv(key: str, default: str = "") -> List[str]:
    raw = os.getenv(key, default)
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


@dataclass(slots=True)
class Settings:
    """
    Central configuration object for the relay.

    NOTE:
    - Fields are stored in UPPERCASE (matching env vars).
    - Lowercase properties are provided as aliases so existing code
      can use e.g. settings.default_model, settings.environment, etc.
    """

    # Project identity
    project_name: str

    # Core relay / app mode
    APP_MODE: str
    ENVIRONMENT: str

    # Logging
    LOG_LEVEL: str
    LOG_FORMAT: str
    LOG_COLOR: bool

    # OpenAI upstream
    OPENAI_API_BASE: str
    OPENAI_API_KEY: str
    OPENAI_ASSISTANTS_BETA: str
    OPENAI_REALTIME_BETA: str
    OPENAI_ORGANIZATION: Optional[str]

    # Default models
    DEFAULT_MODEL: str
    REALTIME_MODEL: str

    # Relay runtime
    RELAY_HOST: str
    RELAY_PORT: int
    RELAY_NAME: str
    RELAY_TIMEOUT: int
    PROXY_TIMEOUT: int
    PYTHON_VERSION: str

    # Streaming / orchestration
    ENABLE_STREAM: bool
    CHAIN_WAIT_MODE: str

    # Auth / secrets
    RELAY_AUTH_ENABLED: bool
    RELAY_KEY: Optional[str]
    CHATGPT_ACTIONS_SECRET: Optional[str]

    # CORS
    CORS_ALLOW_ORIGINS: List[str]
    CORS_ALLOW_METHODS: List[str]
    CORS_ALLOW_HEADERS: List[str]

    # Tools & validation
    TOOLS_MANIFEST: str
    VALIDATION_SCHEMA_PATH: str

    # HTTP client behavior
    timeout_seconds: int
    max_retries: int

    # --------- Convenience alias properties (lowercase) ---------

    @property
    def environment(self) -> str:
        return self.ENVIRONMENT

    @property
    def app_mode(self) -> str:
        return self.APP_MODE

    @property
    def default_model(self) -> str:
        return self.DEFAULT_MODEL

    @property
    def realtime_model(self) -> str:
        return self.REALTIME_MODEL

    @property
    def relay_auth_enabled(self) -> bool:
        return self.RELAY_AUTH_ENABLED

    # 👇 existing alias for the raw value (optional but nice)
    @property
    def openai_api_base(self) -> str:
        return self.OPENAI_API_BASE

    # 👇 NEW: alias expected by http_client.py & forward_openai.py
    @property
    def openai_base_url(self) -> str:
        """
        Backwards‑compatible alias used by the HTTP client and proxy.
        """
        return self.OPENAI_API_BASE

    @property
    def openai_api_key(self) -> str:
        return self.OPENAI_API_KEY

    @property
    def openai_organization(self) -> Optional[str]:
        return self.OPENAI_ORGANIZATION

    @property
    def log_level(self) -> str:
        return self.LOG_LEVEL

    @property
    def cors_allow_origins(self) -> List[str]:
        return self.CORS_ALLOW_ORIGINS

    @property
    def cors_allow_methods(self) -> List[str]:
        return self.CORS_ALLOW_METHODS

    @property
    def cors_allow_headers(self) -> List[str]:
        return self.CORS_ALLOW_HEADERS


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    project_name = "chatgpt-team-relay"

    # Core
    app_mode = _get_env("APP_MODE", "development")
    environment = _get_env("ENVIRONMENT", "development")

    # Logging
    log_level = _get_env("LOG_LEVEL", "info")
    log_format = _get_env("LOG_FORMAT", "console")
    log_color = _get_bool("LOG_COLOR", True)

    # OpenAI upstream
    # Default to official API; you can override with OPENAI_API_BASE in .env
    openai_api_base = _get_env("OPENAI_API_BASE", "https://api.openai.com/v1")
    openai_api_key = _get_env("OPENAI_API_KEY", required=True)
    openai_assistants_beta = _get_env("OPENAI_ASSISTANTS_BETA", "assistants=v2")
    openai_realtime_beta = _get_env("OPENAI_REALTIME_BETA", "realtime=v1")
    openai_organization = os.getenv("OPENAI_ORGANIZATION")

    # Default models
    default_model = _get_env("DEFAULT_MODEL", "gpt-4o-mini")
    realtime_model = _get_env("REALTIME_MODEL", "gpt-4o-realtime-preview")

    # Relay runtime
    relay_host = _get_env("RELAY_HOST", "0.0.0.0")
    relay_port = _get_int("RELAY_PORT", 10000)
    relay_name = _get_env("RELAY_NAME", "ChatGPT Team Relay (local dev)")
    relay_timeout = _get_int("RELAY_TIMEOUT", 120)
    proxy_timeout = _get_int("PROXY_TIMEOUT", 120)
    python_version = _get_env("PYTHON_VERSION", "")

    # Streaming / orchestration
    enable_stream = _get_bool("ENABLE_STREAM", True)
    chain_wait_mode = _get_env("CHAIN_WAIT_MODE", "sequential")

    # Auth / secrets
    relay_auth_enabled = _get_bool(
        "RELAY_AUTH_ENABLED",
        bool(os.getenv("RELAY_KEY") or os.getenv("RELAY_AUTH_TOKEN")),
    )
    relay_key = os.getenv("RELAY_KEY") or os.getenv("RELAY_AUTH_TOKEN")
    chatgpt_actions_secret = os.getenv("CHATGPT_ACTIONS_SECRET")

    # CORS
    cors_allow_origins = _get_csv("CORS_ALLOW_ORIGINS")
    cors_allow_methods = _get_csv("CORS_ALLOW_METHODS")
    cors_allow_headers = _get_csv("CORS_ALLOW_HEADERS")

    # Tools & validation
    tools_manifest = _get_env("TOOLS_MANIFEST", "app/manifests/tools_manifest.json")
    validation_schema_path = _get_env("VALIDATION_SCHEMA_PATH", "")

    # HTTP client behavior
    timeout_seconds = relay_timeout
    max_retries = 3

    return Settings(
        project_name=project_name,
        APP_MODE=app_mode,
        ENVIRONMENT=environment,
        LOG_LEVEL=log_level,
        LOG_FORMAT=log_format,
        LOG_COLOR=log_color,
        OPENAI_API_BASE=openai_api_base,
        OPENAI_API_KEY=openai_api_key,
        OPENAI_ASSISTANTS_BETA=openai_assistants_beta,
        OPENAI_REALTIME_BETA=openai_realtime_beta,
        OPENAI_ORGANIZATION=openai_organization,
        DEFAULT_MODEL=default_model,
        REALTIME_MODEL=realtime_model,
        RELAY_HOST=relay_host,
        RELAY_PORT=relay_port,
        RELAY_NAME=relay_name,
        RELAY_TIMEOUT=relay_timeout,
        PROXY_TIMEOUT=proxy_timeout,
        PYTHON_VERSION=python_version,
        ENABLE_STREAM=enable_stream,
        CHAIN_WAIT_MODE=chain_wait_mode,
        RELAY_AUTH_ENABLED=relay_auth_enabled,
        RELAY_KEY=relay_key,
        CHATGPT_ACTIONS_SECRET=chatgpt_actions_secret,
        CORS_ALLOW_ORIGINS=cors_allow_origins,
        CORS_ALLOW_METHODS=cors_allow_methods,
        CORS_ALLOW_HEADERS=cors_allow_headers,
        TOOLS_MANIFEST=tools_manifest,
        VALIDATION_SCHEMA_PATH=validation_schema_path,
        timeout_seconds=timeout_seconds,
        max_retries=max_retries,
    )


settings: Settings = get_settings()
