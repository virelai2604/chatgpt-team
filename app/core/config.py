# app/core/config.py
from __future__ import annotations

import json
import os
import platform
from dataclasses import dataclass
from functools import lru_cache
from typing import List, Optional


def _env(name: str, default: Optional[str] = None) -> Optional[str]:
    v = os.getenv(name)
    if v is None:
        return default
    v = v.strip()
    return v if v != "" else default


def _env_bool(name: str, default: bool = False) -> bool:
    v = _env(name)
    if v is None:
        return default
    return v.lower() in {"1", "true", "yes", "y", "on"}


def _env_int(name: str, default: int) -> int:
    v = _env(name)
    if v is None:
        return default
    try:
        return int(v)
    except ValueError:
        return default


def _env_list(name: str, default: Optional[List[str]] = None) -> List[str]:
    """
    Accepts:
      - JSON list: '["https://a.com","https://b.com"]'
      - CSV string: 'https://a.com,https://b.com'
      - single value
    """
    default = default or []
    raw = _env(name)
    if raw is None:
        return list(default)

    raw = raw.strip()
    if raw.startswith("["):
        try:
            data = json.loads(raw)
            if isinstance(data, list):
                return [str(x).strip() for x in data if str(x).strip()]
        except Exception:
            return list(default)

    parts = [p.strip() for p in raw.split(",")]
    return [p for p in parts if p]


@dataclass(slots=True)
class Settings:
    # --- Core service identity ---
    APP_MODE: str
    ENVIRONMENT: str
    PROJECT_NAME: str
    RELAY_NAME: str
    BIFL_VERSION: str

    # --- Runtime / diagnostics ---
    PYTHON_VERSION: str
    LOG_LEVEL: str

    # --- OpenAI upstream ---
    OPENAI_API_BASE: str
    OPENAI_API_KEY: str
    DEFAULT_MODEL: str
    REALTIME_MODEL: str

    # --- Auth (relay) ---
    RELAY_AUTH_ENABLED: bool
    RELAY_KEY: Optional[str]
    RELAY_AUTH_TOKEN: Optional[str]  # legacy compatibility

    # --- CORS ---
    CORS_ALLOW_ORIGINS: List[str]
    CORS_ALLOW_METHODS: List[str]
    CORS_ALLOW_HEADERS: List[str]
    CORS_ALLOW_CREDENTIALS: bool

    # --- Tools/manifest ---
    TOOLS_MANIFEST: str

    # --- HTTP timeouts (optional knobs) ---
    HTTP_TIMEOUT_SECONDS: int

    # ---------- Convenience / backward-compatible attribute names ----------
    @property
    def environment(self) -> str:
        return self.ENVIRONMENT

    @property
    def project_name(self) -> str:
        return self.PROJECT_NAME

    @property
    def relay_name(self) -> str:
        return self.RELAY_NAME

    @property
    def version(self) -> str:
        return self.BIFL_VERSION

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

    @property
    def cors_allow_credentials(self) -> bool:
        return self.CORS_ALLOW_CREDENTIALS

    @property
    def openai_base_url(self) -> str:
        return self.OPENAI_API_BASE

    @property
    def openai_api_key(self) -> str:
        return self.OPENAI_API_KEY

    @property
    def default_model(self) -> str:
        return self.DEFAULT_MODEL

    @property
    def realtime_model(self) -> str:
        return self.REALTIME_MODEL


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    # Service identity
    app_mode = _env("APP_MODE", "development")
    environment = _env("ENVIRONMENT", app_mode)
    project_name = _env("PROJECT_NAME", "chatgpt-team-relay")
    relay_name = _env("RELAY_NAME", "ChatGPT Team Relay")
    bifl_version = _env("BIFL_VERSION", "local-dev")

    # Diagnostics
    python_version = _env("PYTHON_VERSION", platform.python_version())
    log_level = _env("LOG_LEVEL", _env("LOGLEVEL", "INFO"))

    # OpenAI upstream
    openai_api_base = _env("OPENAI_API_BASE", "https://api.openai.com/v1")
    openai_api_key = _env("OPENAI_API_KEY", "")  # allow empty for local health/dev; enforce on upstream calls
    default_model = _env("DEFAULT_MODEL", "gpt-5.1")
    realtime_model = _env("REALTIME_MODEL", "gpt-realtime")

    # Relay auth
    relay_auth_enabled = _env_bool("RELAY_AUTH_ENABLED", True)
    relay_key = _env("RELAY_KEY", None)
    relay_auth_token = _env("RELAY_AUTH_TOKEN", None)

    # CORS
    cors_allow_origins = _env_list("CORS_ALLOW_ORIGINS", default=["*"])
    cors_allow_methods = _env_list("CORS_ALLOW_METHODS", default=["*"])
    cors_allow_headers = _env_list("CORS_ALLOW_HEADERS", default=["*"])
    cors_allow_credentials = _env_bool("CORS_ALLOW_CREDENTIALS", False)

    # Tools / manifest
    tools_manifest = _env("TOOLS_MANIFEST", "tools_manifest.json")

    # HTTP
    http_timeout_seconds = _env_int("HTTP_TIMEOUT_SECONDS", 90)

    return Settings(
        APP_MODE=app_mode,
        ENVIRONMENT=environment,
        PROJECT_NAME=project_name,
        RELAY_NAME=relay_name,
        BIFL_VERSION=bifl_version,
        PYTHON_VERSION=python_version,
        LOG_LEVEL=log_level,
        OPENAI_API_BASE=openai_api_base,
        OPENAI_API_KEY=openai_api_key,
        DEFAULT_MODEL=default_model,
        REALTIME_MODEL=realtime_model,
        RELAY_AUTH_ENABLED=relay_auth_enabled,
        RELAY_KEY=relay_key,
        RELAY_AUTH_TOKEN=relay_auth_token,
        CORS_ALLOW_ORIGINS=cors_allow_origins,
        CORS_ALLOW_METHODS=cors_allow_methods,
        CORS_ALLOW_HEADERS=cors_allow_headers,
        CORS_ALLOW_CREDENTIALS=cors_allow_credentials,
        TOOLS_MANIFEST=tools_manifest,
        HTTP_TIMEOUT_SECONDS=http_timeout_seconds,
    )


# Keep the legacy singleton import pattern used across the codebase
settings = get_settings()
