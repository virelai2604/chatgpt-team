from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import List, Optional


def _env(key: str, default: Optional[str] = None) -> str:
    val = os.getenv(key)
    if val is None:
        return "" if default is None else default
    return val


def _bool_env(key: str, default: bool = False) -> bool:
    val = os.getenv(key)
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "yes", "y", "on")


def _csv_env(key: str, default: Optional[List[str]] = None) -> List[str]:
    val = os.getenv(key)
    if not val:
        return list(default or [])
    return [x.strip() for x in val.split(",") if x.strip()]


def _normalize_url(url: str) -> str:
    return (url or "").strip().rstrip("/")


def _strip_v1(url: str) -> str:
    url = _normalize_url(url)
    if url.endswith("/v1"):
        return url[:-3].rstrip("/")
    return url


@dataclass(slots=True)
class Settings:
    # --- App / relay identity ---
    app_mode: str = field(default_factory=lambda: _env("APP_MODE", "dev"))
    relay_name: str = field(default_factory=lambda: _env("RELAY_NAME", "openai-relay"))

    # --- OpenAI / upstream configuration (canonical = lower_snake_case) ---
    openai_api_key: str = field(default_factory=lambda: _env("OPENAI_API_KEY", ""))
    openai_organization: str = field(
        default_factory=lambda: _env("OPENAI_ORG_ID", _env("OPENAI_ORGANIZATION", ""))
    )
    openai_project: str = field(default_factory=lambda: _env("OPENAI_PROJECT_ID", ""))
    openai_beta: str = field(default_factory=lambda: _env("OPENAI_BETA", ""))

    # Root base URL (no /v1) and API base URL (includes /v1). You can set either:
    # - OPENAI_BASE_URL=https://api.openai.com
    # - OPENAI_API_BASE=https://api.openai.com/v1
    openai_base_url: str = field(default_factory=lambda: _env("OPENAI_BASE_URL", ""))
    openai_api_base: str = field(
        default_factory=lambda: _env("OPENAI_API_BASE", "https://api.openai.com/v1")
    )

    # --- Relay auth / runtime ---
    relay_auth_enabled: bool = field(default_factory=lambda: _bool_env("RELAY_AUTH_ENABLED", False))
    relay_key: str = field(default_factory=lambda: _env("RELAY_KEY", ""))
    relay_auth_header: str = field(default_factory=lambda: _env("RELAY_AUTH_HEADER", "X-Relay-Key"))
    relay_timeout_seconds: float = field(default_factory=lambda: float(_env("RELAY_TIMEOUT_SECONDS", "120")))

    # --- Defaults / misc ---
    default_model: str = field(default_factory=lambda: _env("DEFAULT_MODEL", _env("RELAY_MODEL", "gpt-5.1")))

    cors_allow_origins: List[str] = field(default_factory=lambda: _csv_env("CORS_ALLOW_ORIGINS", ["*"]))
    cors_allow_methods: List[str] = field(default_factory=lambda: _csv_env("CORS_ALLOW_METHODS", ["*"]))
    cors_allow_headers: List[str] = field(default_factory=lambda: _csv_env("CORS_ALLOW_HEADERS", ["*"]))
    cors_allow_credentials: bool = field(default_factory=lambda: _bool_env("CORS_ALLOW_CREDENTIALS", True))

    log_level: str = field(default_factory=lambda: _env("LOG_LEVEL", "INFO"))
    environment: str = field(default_factory=lambda: _env("ENVIRONMENT", "dev"))

    def __post_init__(self) -> None:
        # Normalize and reconcile URLs.
        self.openai_base_url = _normalize_url(self.openai_base_url)
        self.openai_api_base = _normalize_url(self.openai_api_base)

        if self.openai_base_url:
            self.openai_api_base = f"{self.openai_base_url}/v1"
        else:
            base = _strip_v1(self.openai_api_base)
            self.openai_base_url = base or "https://api.openai.com"
            self.openai_api_base = f"{self.openai_base_url}/v1"

        # Best-effort logging level (do not crash if logging misconfigured).
        try:
            logging.getLogger().setLevel(self.log_level.upper())
        except Exception:
            pass

    def validate(self) -> None:
        if not self.openai_base_url:
            raise ValueError("openai_base_url must not be empty")
        if self.relay_auth_enabled and not self.relay_key:
            raise ValueError("RELAY_AUTH_ENABLED=true requires RELAY_KEY")

    def upstream_headers(self) -> dict:
        headers = {"Authorization": f"Bearer {self.openai_api_key}"}
        if self.openai_organization:
            headers["OpenAI-Organization"] = self.openai_organization
        if self.openai_project:
            headers["OpenAI-Project"] = self.openai_project
        if self.openai_beta:
            headers["OpenAI-Beta"] = self.openai_beta
        return headers

    # ---------------------------------------------------------------------
    # Uppercase aliases (compat with older code / tests).
    # Include setters so tests can monkeypatch them.
    # ---------------------------------------------------------------------
    @property
    def APP_MODE(self) -> str:
        return self.app_mode

    @APP_MODE.setter
    def APP_MODE(self, value: str) -> None:
        self.app_mode = value or self.app_mode

    @property
    def RELAY_NAME(self) -> str:
        return self.relay_name

    @RELAY_NAME.setter
    def RELAY_NAME(self, value: str) -> None:
        self.relay_name = value or self.relay_name

    @property
    def OPENAI_API_KEY(self) -> str:
        return self.openai_api_key

    @OPENAI_API_KEY.setter
    def OPENAI_API_KEY(self, value: str) -> None:
        self.openai_api_key = value or ""

    @property
    def OPENAI_ORG_ID(self) -> str:
        return self.openai_organization

    @OPENAI_ORG_ID.setter
    def OPENAI_ORG_ID(self, value: str) -> None:
        self.openai_organization = value or ""

    @property
    def OPENAI_PROJECT_ID(self) -> str:
        return self.openai_project

    @OPENAI_PROJECT_ID.setter
    def OPENAI_PROJECT_ID(self, value: str) -> None:
        self.openai_project = value or ""

    @property
    def OPENAI_API_BASE(self) -> str:
        return self.openai_api_base

    @OPENAI_API_BASE.setter
    def OPENAI_API_BASE(self, value: str) -> None:
        api_base = _normalize_url(value)
        base = _strip_v1(api_base)
        self.openai_base_url = base or "https://api.openai.com"
        self.openai_api_base = f"{self.openai_base_url}/v1"

    @property
    def UPSTREAM_BASE_URL(self) -> str:
        return self.openai_base_url

    @UPSTREAM_BASE_URL.setter
    def UPSTREAM_BASE_URL(self, value: str) -> None:
        base = _normalize_url(value)
        self.openai_base_url = base or "https://api.openai.com"
        self.openai_api_base = f"{self.openai_base_url}/v1"

    @property
    def RELAY_AUTH_ENABLED(self) -> bool:
        return self.relay_auth_enabled

    @RELAY_AUTH_ENABLED.setter
    def RELAY_AUTH_ENABLED(self, value: bool) -> None:
        self.relay_auth_enabled = bool(value)

    @property
    def RELAY_KEY(self) -> str:
        return self.relay_key

    @RELAY_KEY.setter
    def RELAY_KEY(self, value: str) -> None:
        self.relay_key = value or ""

    @property
    def RELAY_AUTH_HEADER(self) -> str:
        return self.relay_auth_header

    @RELAY_AUTH_HEADER.setter
    def RELAY_AUTH_HEADER(self, value: str) -> None:
        self.relay_auth_header = value or "X-Relay-Key"

    @property
    def RELAY_TIMEOUT_SECONDS(self) -> float:
        return self.relay_timeout_seconds

    @RELAY_TIMEOUT_SECONDS.setter
    def RELAY_TIMEOUT_SECONDS(self, value: float) -> None:
        self.relay_timeout_seconds = float(value)

    @property
    def DEFAULT_MODEL(self) -> str:
        return self.default_model

    @DEFAULT_MODEL.setter
    def DEFAULT_MODEL(self, value: str) -> None:
        self.default_model = value or self.default_model

    @property
    def CORS_ALLOW_ORIGINS(self) -> List[str]:
        return self.cors_allow_origins

    @CORS_ALLOW_ORIGINS.setter
    def CORS_ALLOW_ORIGINS(self, value: List[str]) -> None:
        self.cors_allow_origins = list(value or [])

    @property
    def CORS_ALLOW_METHODS(self) -> List[str]:
        return self.cors_allow_methods

    @CORS_ALLOW_METHODS.setter
    def CORS_ALLOW_METHODS(self, value: List[str]) -> None:
        self.cors_allow_methods = list(value or [])

    @property
    def CORS_ALLOW_HEADERS(self) -> List[str]:
        return self.cors_allow_headers

    @CORS_ALLOW_HEADERS.setter
    def CORS_ALLOW_HEADERS(self, value: List[str]) -> None:
        self.cors_allow_headers = list(value or [])

    @property
    def CORS_ALLOW_CREDENTIALS(self) -> bool:
        return self.cors_allow_credentials

    @CORS_ALLOW_CREDENTIALS.setter
    def CORS_ALLOW_CREDENTIALS(self, value: bool) -> None:
        self.cors_allow_credentials = bool(value)

    @property
    def LOG_LEVEL(self) -> str:
        return self.log_level

    @LOG_LEVEL.setter
    def LOG_LEVEL(self, value: str) -> None:
        self.log_level = value or self.log_level

    @property
    def ENVIRONMENT(self) -> str:
        return self.environment

    @ENVIRONMENT.setter
    def ENVIRONMENT(self, value: str) -> None:
        self.environment = value or self.environment

    # Back-compat: some older code referenced this attribute name.
    @property
    def proxy_timeout_seconds(self) -> float:
        return self.relay_timeout_seconds

    @proxy_timeout_seconds.setter
    def proxy_timeout_seconds(self, value: float) -> None:
        self.relay_timeout_seconds = float(value)


_settings_cache: Optional[Settings] = None


def get_settings() -> Settings:
    global _settings_cache
    if _settings_cache is None:
        _settings_cache = Settings()
        _settings_cache.validate()
    return _settings_cache


# Convenience singleton (tests may monkeypatch attributes on this instance)
settings = get_settings()

# Local logger for modules that import it from here.
logger = logging.getLogger("relay")
