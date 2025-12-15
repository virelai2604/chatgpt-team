from __future__ import annotations

import json
import os
import platform
from dataclasses import dataclass
from functools import lru_cache
from typing import List, Optional


def _env(name: str, default: Optional[str] = None) -> Optional[str]:
    """Read an environment variable with whitespace/empty-string normalization."""
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
                out = [str(x).strip() for x in data]
                return [x for x in out if x]
        except Exception:
            return list(default)

    parts = [p.strip() for p in raw.split(",")]
    return [p for p in parts if p]


@dataclass(slots=True)
class Settings:
    # Core service identity
    APP_MODE: str
    ENVIRONMENT: str
    PROJECT_NAME: str
    RELAY_NAME: str
    BIFL_VERSION: str

    # Runtime / diagnostics
    PYTHON_VERSION: str
    LOG_LEVEL: str
    LOG_FORMAT: str
    LOG_COLOR: bool

    # OpenAI upstream
    OPENAI_API_BASE: str
    OPENAI_API_KEY: str
    OPENAI_ORGANIZATION: Optional[str]
    OPENAI_PROJECT: Optional[str]
    OPENAI_BETA: Optional[str]
    OPENAI_ASSISTANTS_BETA: Optional[str]
    OPENAI_REALTIME_BETA: Optional[str]
    OPENAI_MAX_RETRIES: int

    DEFAULT_MODEL: str
    REALTIME_MODEL: str

    # Relay runtime
    RELAY_HOST: str
    RELAY_PORT: int
    RELAY_TIMEOUT_SECONDS: int
    PROXY_TIMEOUT_SECONDS: int

    # Stream / orchestration
    ENABLE_STREAM: bool
    CHAIN_WAIT_MODE: str

    # Relay auth
    RELAY_AUTH_ENABLED: bool
    RELAY_KEY: Optional[str]
    CHATGPT_ACTIONS_SECRET: Optional[str]
    RELAY_AUTH_TOKEN: Optional[str]

    # CORS
    CORS_ALLOW_ORIGINS: List[str]
    CORS_ALLOW_METHODS: List[str]
    CORS_ALLOW_HEADERS: List[str]
    CORS_ALLOW_CREDENTIALS: bool

    # Tools / schema
    TOOLS_MANIFEST: str
    VALIDATION_SCHEMA_PATH: Optional[str]

    # Convenience aliases (snake_case)
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
    def openai_organization(self) -> Optional[str]:
        return self.OPENAI_ORGANIZATION

    @property
    def openai_project(self) -> Optional[str]:
        return self.OPENAI_PROJECT

    @property
    def openai_beta(self) -> Optional[str]:
        return self.OPENAI_BETA

    @property
    def openai_assistants_beta(self) -> Optional[str]:
        return self.OPENAI_ASSISTANTS_BETA

    @property
    def openai_realtime_beta(self) -> Optional[str]:
        return self.OPENAI_REALTIME_BETA

    @property
    def default_model(self) -> str:
        return self.DEFAULT_MODEL

    @property
    def realtime_model(self) -> str:
        return self.REALTIME_MODEL

    @property
    def proxy_timeout_seconds(self) -> int:
        return self.PROXY_TIMEOUT_SECONDS

    @property
    def timeout_seconds(self) -> int:
        # Backward compatible alias
        return self.PROXY_TIMEOUT_SECONDS

    @property
    def max_retries(self) -> int:
        return self.OPENAI_MAX_RETRIES


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    app_mode = _env("APP_MODE", "development") or "development"
    environment = _env("ENVIRONMENT", app_mode) or app_mode

    project_name = _env("PROJECT_NAME", "chatgpt-team-relay") or "chatgpt-team-relay"
    relay_name = _env("RELAY_NAME", "ChatGPT Team Relay") or "ChatGPT Team Relay"
    bifl_version = _env("BIFL_VERSION", "local-dev") or "local-dev"

    python_version = _env("PYTHON_VERSION", platform.python_version()) or platform.python_version()
    log_level = _env("LOG_LEVEL", _env("LOGLEVEL", "INFO") or "INFO") or "INFO"
    log_format = _env("LOG_FORMAT", "plain") or "plain"
    log_color = _env_bool("LOG_COLOR", False)

    openai_api_base = _env("OPENAI_API_BASE", "https://api.openai.com/v1") or "https://api.openai.com/v1"
    # Allow empty key at import-time; enforce on upstream call sites.
    openai_api_key = _env("OPENAI_API_KEY", "") or ""
    openai_org = _env("OPENAI_ORGANIZATION", _env("OPENAI_ORG", None))
    openai_project = _env("OPENAI_PROJECT", None)
    openai_beta = _env("OPENAI_BETA", None)
    openai_assistants_beta = _env("OPENAI_ASSISTANTS_BETA", None)
    openai_realtime_beta = _env("OPENAI_REALTIME_BETA", None)
    openai_max_retries = _env_int("OPENAI_MAX_RETRIES", 3)

    default_model = _env("DEFAULT_MODEL", "gpt-5.1") or "gpt-5.1"
    realtime_model = _env("REALTIME_MODEL", "gpt-realtime") or "gpt-realtime"

    relay_host = _env("RELAY_HOST", "0.0.0.0") or "0.0.0.0"
    relay_port = _env_int("RELAY_PORT", 8000)
    relay_timeout_seconds = _env_int("RELAY_TIMEOUT_SECONDS", _env_int("RELAY_TIMEOUT", 90))
    proxy_timeout_seconds = _env_int("PROXY_TIMEOUT_SECONDS", _env_int("PROXY_TIMEOUT", 90))

    enable_stream = _env_bool("ENABLE_STREAM", True)
    chain_wait_mode = _env("CHAIN_WAIT_MODE", "auto") or "auto"

    relay_auth_enabled = _env_bool("RELAY_AUTH_ENABLED", True)
    relay_key = _env("RELAY_KEY", None)
    chatgpt_actions_secret = _env("CHATGPT_ACTIONS_SECRET", None)
    relay_auth_token = _env("RELAY_AUTH_TOKEN", None)

    cors_allow_origins = _env_list("CORS_ALLOW_ORIGINS", default=["*"])
    cors_allow_methods = _env_list("CORS_ALLOW_METHODS", default=["*"])
    cors_allow_headers = _env_list("CORS_ALLOW_HEADERS", default=["*"])
    cors_allow_credentials = _env_bool("CORS_ALLOW_CREDENTIALS", False)

    tools_manifest = _env("TOOLS_MANIFEST", "tools_manifest.json") or "tools_manifest.json"
    validation_schema_path = _env("VALIDATION_SCHEMA_PATH", None)

    return Settings(
        APP_MODE=app_mode,
        ENVIRONMENT=environment,
        PROJECT_NAME=project_name,
        RELAY_NAME=relay_name,
        BIFL_VERSION=bifl_version,
        PYTHON_VERSION=python_version,
        LOG_LEVEL=log_level,
        LOG_FORMAT=log_format,
        LOG_COLOR=log_color,
        OPENAI_API_BASE=openai_api_base,
        OPENAI_API_KEY=openai_api_key,
        OPENAI_ORGANIZATION=openai_org,
        OPENAI_PROJECT=openai_project,
        OPENAI_BETA=openai_beta,
        OPENAI_ASSISTANTS_BETA=openai_assistants_beta,
        OPENAI_REALTIME_BETA=openai_realtime_beta,
        OPENAI_MAX_RETRIES=openai_max_retries,
        DEFAULT_MODEL=default_model,
        REALTIME_MODEL=realtime_model,
        RELAY_HOST=relay_host,
        RELAY_PORT=relay_port,
        RELAY_TIMEOUT_SECONDS=relay_timeout_seconds,
        PROXY_TIMEOUT_SECONDS=proxy_timeout_seconds,
        ENABLE_STREAM=enable_stream,
        CHAIN_WAIT_MODE=chain_wait_mode,
        RELAY_AUTH_ENABLED=relay_auth_enabled,
        RELAY_KEY=relay_key,
        CHATGPT_ACTIONS_SECRET=chatgpt_actions_secret,
        RELAY_AUTH_TOKEN=relay_auth_token,
        CORS_ALLOW_ORIGINS=cors_allow_origins,
        CORS_ALLOW_METHODS=cors_allow_methods,
        CORS_ALLOW_HEADERS=cors_allow_headers,
        CORS_ALLOW_CREDENTIALS=cors_allow_credentials,
        TOOLS_MANIFEST=tools_manifest,
        VALIDATION_SCHEMA_PATH=validation_schema_path,
    )


# Legacy singleton import pattern used across the codebase
settings: Settings = get_settings()
