from __future__ import annotations

import json
import os
from dataclasses import dataclass
from functools import lru_cache
from typing import List, Optional


def _get_env(
    key: str,
    default: Optional[str] = None,
    *,
    required: bool = False,
) -> Optional[str]:
    """
    Read an environment variable as a string.

    - Treats unset or blank values as "missing".
    - If required=True and missing, raises RuntimeError.
    """
    value = os.getenv(key)
    if value is None:
        if required:
            raise RuntimeError(f"Missing required environment variable: {key}")
        return default

    value = value.strip()
    if value == "":
        if required:
            raise RuntimeError(f"Missing required environment variable: {key}")
        return default

    return value


def _get_int(key: str, default: int) -> int:
    raw = os.getenv(key)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw.strip())
    except ValueError:
        return default


def _get_bool(key: str, default: bool) -> bool:
    raw = os.getenv(key)
    if raw is None:
        return default

    raw = raw.strip().lower()
    if raw in ("1", "true", "t", "yes", "y", "on"):
        return True
    if raw in ("0", "false", "f", "no", "n", "off"):
        return False

    return default


def _parse_list(raw: str) -> List[str]:
    """
    Parse a list-like env var.

    Accepts:
      - JSON array:  '["a","b"]'
      - CSV:         'a,b'
      - Star:        '*'
    """
    raw = raw.strip()
    if raw == "":
        return []
    if raw == "*":
        return ["*"]

    # Prefer JSON arrays when provided.
    if raw.startswith("[") and raw.endswith("]"):
        try:
            val = json.loads(raw)
            if isinstance(val, list):
                return [str(x).strip() for x in val if str(x).strip() != ""]
        except Exception:
            # fall back to CSV parsing
            pass

    # CSV fallback
    return [item.strip() for item in raw.split(",") if item.strip()]


def _get_list(key: str, default: Optional[List[str]] = None) -> List[str]:
    raw = os.getenv(key)
    if raw is None or raw.strip() == "":
        return list(default) if default is not None else []
    parsed = _parse_list(raw)
    if parsed:
        return parsed
    return list(default) if default is not None else []


@dataclass
class Settings:
    # Meta
    project_name: str

    # Core
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
    OPENAI_PROJECT: Optional[str]

    # Models
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
    RELAY_AUTH_TOKEN: Optional[str]

    # CORS
    CORS_ALLOW_ORIGINS: List[str]
    CORS_ALLOW_METHODS: List[str]
    CORS_ALLOW_HEADERS: List[str]
    CORS_ALLOW_CREDENTIALS: bool

    # Tools / validation
    TOOLS_MANIFEST: str
    VALIDATION_SCHEMA_PATH: str

    # HTTP client behavior
    timeout_seconds: int
    max_retries: int

    # --------------------------
    # Compatibility aliases
    # --------------------------

    @property
    def app_mode(self) -> str:
        return self.APP_MODE

    @property
    def environment(self) -> str:
        return self.ENVIRONMENT

    @property
    def log_level(self) -> str:
        return self.LOG_LEVEL

    @log_level.setter
    def log_level(self, value: str) -> None:
        self.LOG_LEVEL = value

    @property
    def relay_name(self) -> str:
        return self.RELAY_NAME

    @relay_name.setter
    def relay_name(self, value: str) -> None:
        self.RELAY_NAME = value

    @property
    def openai_api_key(self) -> str:
        return self.OPENAI_API_KEY

    @openai_api_key.setter
    def openai_api_key(self, value: str) -> None:
        self.OPENAI_API_KEY = value

    @property
    def openai_base_url(self) -> str:
        return self.OPENAI_API_BASE

    @openai_base_url.setter
    def openai_base_url(self, value: str) -> None:
        self.OPENAI_API_BASE = value

    @property
    def openai_assistants_beta(self) -> str:
        return self.OPENAI_ASSISTANTS_BETA

    @property
    def openai_realtime_beta(self) -> str:
        return self.OPENAI_REALTIME_BETA

    @property
    def openai_organization(self) -> Optional[str]:
        return self.OPENAI_ORGANIZATION

    @property
    def openai_project(self) -> Optional[str]:
        return self.OPENAI_PROJECT

    @property
    def default_model(self) -> str:
        return self.DEFAULT_MODEL

    @default_model.setter
    def default_model(self, value: str) -> None:
        self.DEFAULT_MODEL = value

    @property
    def realtime_model(self) -> str:
        return self.REALTIME_MODEL

    @realtime_model.setter
    def realtime_model(self, value: str) -> None:
        self.REALTIME_MODEL = value

    @property
    def relay_timeout_seconds(self) -> int:
        return self.RELAY_TIMEOUT

    @property
    def proxy_timeout_seconds(self) -> int:
        return self.PROXY_TIMEOUT

    @property
    def relay_auth_enabled(self) -> bool:
        return self.RELAY_AUTH_ENABLED

    @relay_auth_enabled.setter
    def relay_auth_enabled(self, value: bool) -> None:
        self.RELAY_AUTH_ENABLED = bool(value)

    @property
    def relay_key(self) -> Optional[str]:
        return self.RELAY_KEY

    @relay_key.setter
    def relay_key(self, value: Optional[str]) -> None:
        self.RELAY_KEY = value

    # Some modules expect this exact attribute name.
    @property
    def UPSTREAM_BASE_URL(self) -> str:
        return self.OPENAI_API_BASE

    @UPSTREAM_BASE_URL.setter
    def UPSTREAM_BASE_URL(self, value: str) -> None:
        self.OPENAI_API_BASE = value

    @property
    def tools_manifest(self) -> str:
        return self.TOOLS_MANIFEST

    @tools_manifest.setter
    def tools_manifest(self, value: str) -> None:
        self.TOOLS_MANIFEST = value

    @property
    def validation_schema_path(self) -> str:
        return self.VALIDATION_SCHEMA_PATH

    @validation_schema_path.setter
    def validation_schema_path(self, value: str) -> None:
        self.VALIDATION_SCHEMA_PATH = value

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


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    project_name = "chatgpt-team-relay"

    app_mode = _get_env("APP_MODE", "development") or "development"
    environment = _get_env("ENVIRONMENT", "development") or "development"

    log_level = (_get_env("LOG_LEVEL", "info") or "info").lower()
    log_format = _get_env("LOG_FORMAT", "console") or "console"
    log_color = _get_bool("LOG_COLOR", True)

    openai_api_base = _get_env("OPENAI_API_BASE", "https://api.openai.com") or "https://api.openai.com"
    # Allow empty key so the server can start; forwarder should reject requests if missing.
    openai_api_key = _get_env("OPENAI_API_KEY", "") or ""
    openai_assistants_beta = _get_env("OPENAI_ASSISTANTS_BETA", "assistants=v2") or "assistants=v2"
    openai_realtime_beta = _get_env("OPENAI_REALTIME_BETA", "realtime=v1") or "realtime=v1"
    openai_organization = os.getenv("OPENAI_ORGANIZATION")
    openai_project = os.getenv("OPENAI_PROJECT")

    default_model = _get_env("DEFAULT_MODEL", "gpt-4o-mini") or "gpt-4o-mini"
    realtime_model = _get_env("REALTIME_MODEL", "gpt-4o-realtime-preview") or "gpt-4o-realtime-preview"

    relay_host = _get_env("RELAY_HOST", "0.0.0.0") or "0.0.0.0"
    relay_port = _get_int("RELAY_PORT", 8000)
    relay_name = _get_env("RELAY_NAME", "ChatGPT Team Relay (local dev)") or "ChatGPT Team Relay (local dev)"
    relay_timeout = _get_int("RELAY_TIMEOUT", 120)
    proxy_timeout = _get_int("PROXY_TIMEOUT", 120)
    python_version = _get_env("PYTHON_VERSION", "") or ""

    enable_stream = _get_bool("ENABLE_STREAM", True)
    chain_wait_mode = _get_env("CHAIN_WAIT_MODE", "sequential") or "sequential"

    relay_key = os.getenv("RELAY_KEY") or None
    relay_auth_token = os.getenv("RELAY_AUTH_TOKEN") or None
    chatgpt_actions_secret = os.getenv("CHATGPT_ACTIONS_SECRET")

    # Safer default: if RELAY_AUTH_ENABLED isn't set, enable it only when a key exists.
    relay_auth_enabled = _get_bool("RELAY_AUTH_ENABLED", bool(relay_key or relay_auth_token))

    cors_allow_origins = _get_list("CORS_ALLOW_ORIGINS", default=["*"])
    cors_allow_methods = _get_list("CORS_ALLOW_METHODS", default=["*"])
    cors_allow_headers = _get_list("CORS_ALLOW_HEADERS", default=["*"])
    cors_allow_credentials = _get_bool("CORS_ALLOW_CREDENTIALS", True)

    tools_manifest = _get_env("TOOLS_MANIFEST", "app/manifests/tools_manifest.json") or "app/manifests/tools_manifest.json"
    validation_schema_path = _get_env("VALIDATION_SCHEMA_PATH", "") or ""

    timeout_seconds = relay_timeout
    max_retries = _get_int("MAX_RETRIES", 3)

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
        OPENAI_PROJECT=openai_project,
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
        RELAY_AUTH_TOKEN=relay_auth_token,
        CORS_ALLOW_ORIGINS=cors_allow_origins,
        CORS_ALLOW_METHODS=cors_allow_methods,
        CORS_ALLOW_HEADERS=cors_allow_headers,
        CORS_ALLOW_CREDENTIALS=cors_allow_credentials,
        TOOLS_MANIFEST=tools_manifest,
        VALIDATION_SCHEMA_PATH=validation_schema_path,
        timeout_seconds=timeout_seconds,
        max_retries=max_retries,
    )


settings: Settings = get_settings()
