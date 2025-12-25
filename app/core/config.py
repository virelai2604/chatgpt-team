from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from functools import lru_cache


def _env(name: str, default: str = "") -> str:
    value = os.getenv(name)
    return default if value is None else value


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}


def _env_list(name: str, default: list[str] | None = None) -> list[str]:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return list(default or [])
    s = raw.strip()
    # Allow either CSV ("a,b,c") or a JSON array ('["a","b"]').
    if s.startswith("["):
        try:
            loaded = json.loads(s)
            if isinstance(loaded, list):
                return [str(x).strip() for x in loaded if str(x).strip()]
        except Exception:
            pass
    return [p.strip() for p in s.split(",") if p.strip()]


@dataclass(frozen=True)
class Settings:
    # App identity / environment
    APP_MODE: str = field(default_factory=lambda: _env("APP_MODE", "local"))
    ENVIRONMENT: str = field(default_factory=lambda: _env("ENVIRONMENT", "dev"))
    RELAY_NAME: str = field(default_factory=lambda: _env("RELAY_NAME", "chatgpt-team relay"))

    # OpenAI upstream
    OPENAI_API_KEY: str = field(default_factory=lambda: _env("OPENAI_API_KEY", ""))
    OPENAI_API_BASE: str = field(default_factory=lambda: _env("OPENAI_API_BASE", "https://api.openai.com/v1"))
    OPENAI_ORG: str | None = field(default_factory=lambda: _env("OPENAI_ORG", "") or None)
    OPENAI_PROJECT: str | None = field(default_factory=lambda: _env("OPENAI_PROJECT", "") or None)

    DEFAULT_MODEL: str = field(default_factory=lambda: _env("DEFAULT_MODEL", "gpt-4.1-mini"))
    REALTIME_MODEL: str = field(default_factory=lambda: _env("REALTIME_MODEL", "gpt-4.1-mini"))

    # Feature flags
    UPLOADS_ENABLED: bool = field(default_factory=lambda: _env_bool("UPLOADS_ENABLED", True))
    BATCHES_ENABLED: bool = field(default_factory=lambda: _env_bool("BATCHES_ENABLED", True))

    # Timeouts
    RELAY_TIMEOUT: float = field(default_factory=lambda: float(_env("RELAY_TIMEOUT", "120")))

    # Relay auth (preferred header: X-Relay-Key; also accept Authorization: Bearer <key>)
    RELAY_AUTH_ENABLED: bool = field(default_factory=lambda: _env_bool("RELAY_AUTH_ENABLED", False))
    RELAY_KEY: str = field(default_factory=lambda: _env("RELAY_KEY", ""))
    # Legacy env var used by earlier iterations; keep as a fallback.
    RELAY_AUTH_TOKEN: str = field(default_factory=lambda: _env("RELAY_AUTH_TOKEN", ""))

    # Proxy behavior
    BYPASS_UPSTREAM_AUTH: bool = field(default_factory=lambda: _env_bool("BYPASS_UPSTREAM_AUTH", False))
    ENABLE_PROXY: bool = field(default_factory=lambda: _env_bool("ENABLE_PROXY", True))
    PROXY_BLOCKLIST_MODE: bool = field(default_factory=lambda: _env_bool("PROXY_BLOCKLIST_MODE", True))
    PROXY_ALLOWLIST_MODELS: list[str] = field(
        default_factory=lambda: _env_list(
            "PROXY_ALLOWLIST_MODELS",
            default=["gpt-4.1-mini", "gpt-4.1", "gpt-5.1"],
        )
    )

    # CORS (mostly for browser-based local tooling; not required for ChatGPT Actions)
    CORS_ALLOW_ORIGINS: list[str] = field(default_factory=lambda: _env_list("CORS_ALLOW_ORIGINS", default=["*"]))
    CORS_ALLOW_METHODS: list[str] = field(default_factory=lambda: _env_list("CORS_ALLOW_METHODS", default=["*"]))
    CORS_ALLOW_HEADERS: list[str] = field(default_factory=lambda: _env_list("CORS_ALLOW_HEADERS", default=["*"]))
    CORS_ALLOW_CREDENTIALS: bool = field(default_factory=lambda: _env_bool("CORS_ALLOW_CREDENTIALS", False))

    # Tool manifest / validation schemas
    LOG_LEVEL: str = field(default_factory=lambda: _env("LOG_LEVEL", "INFO"))
    TOOLS_MANIFEST: str = field(default_factory=lambda: _env("TOOLS_MANIFEST", "static/tools_manifest.json"))
    VALIDATION_SCHEMA_PATH: str = field(default_factory=lambda: _env("VALIDATION_SCHEMA_PATH", "schemas/relay.schema.json"))

    @property
    def UPSTREAM_BASE_URL(self) -> str:
        """
        Back-compat alias used by some helper endpoints.

        Prefer OPENAI_API_BASE internally. Defaults to the same value.
        """
        return _env("UPSTREAM_BASE_URL", self.OPENAI_API_BASE)

    @property
    def RELAY_AUTH_KEY(self) -> str:
        """Back-compat alias (older name)."""
        return self.RELAY_KEY or self.RELAY_AUTH_TOKEN


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


# Convenience singleton used across modules.
settings = get_settings()
