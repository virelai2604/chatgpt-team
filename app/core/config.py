# app/core/config.py
from __future__ import annotations

import platform
from functools import lru_cache
from typing import Optional

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central configuration for the ChatGPT Team Relay.

    All values are loaded from environment variables or `.env`.
    This model is the single source of truth for:
      - OpenAI upstream configuration (v1/v2 & realtime)
      - Relay identity, timeouts, streaming/chain behavior
      - CORS policy for ChatGPT / platform usage
      - Tools manifest and validation schema (PDF) path
      - Logging and environment metadata
    """

    # -------------------------------------------------------------------------
    # Core environment / app mode
    # -------------------------------------------------------------------------

    APP_MODE: str = Field(
        default="development",
        description="High-level mode (development / production / test).",
    )
    ENVIRONMENT: str = Field(
        default="development",
        description="Deployment environment label (e.g., local, staging, prod).",
    )

    # -------------------------------------------------------------------------
    # Logging configuration
    # -------------------------------------------------------------------------

    LOG_LEVEL: str = Field(
        default="info",
        description="Root log level (debug, info, warning, error, critical).",
    )
    LOG_FORMAT: str = Field(
        default="console",
        description="Logging format (console/json/etc).",
    )
    LOG_COLOR: bool = Field(
        default=True,
        description="Whether to emit colorized logs in console mode.",
    )

    # -------------------------------------------------------------------------
    # OpenAI upstream configuration
    # -------------------------------------------------------------------------

    # IMPORTANT: no `/v1` suffix – the client/forwarder appends paths as needed.
    OPENAI_API_BASE: AnyHttpUrl = Field(
        default="https://api.openai.com",
        description="Base URL for OpenAI API (no trailing /v1).",
    )

    OPENAI_API_KEY: str = Field(
        default="sk-proj-REPLACE_WITH_YOUR_LOCAL_KEY",
        description="Project or account API key used to call OpenAI upstream.",
    )

    # OpenAI-Beta headers for Assistants / Realtime features
    OPENAI_ASSISTANTS_BETA: str = Field(
        default="assistants=v2",
        description="Value for OpenAI-Beta header when using Assistants/Responses v2.",
    )

    OPENAI_REALTIME_BETA: str = Field(
        default="realtime=v1",
        description="Value for OpenAI-Beta header when using realtime endpoints.",
    )

    # Default model choices used in health endpoints and fallbacks
    DEFAULT_MODEL: str = Field(
        default="gpt-4.1-mini",
        description="Default text/chat model when caller does not specify one.",
    )

    REALTIME_MODEL: str = Field(
        default="gpt-4o-realtime-preview",
        description="Default realtime model for websocket/SIP usage.",
    )

    PYTHON_VERSION: str = Field(
        default_factory=platform.python_version,
        description="Python runtime version surfaced in /health.",
    )

    # -------------------------------------------------------------------------
    # Relay timeouts, streaming, and orchestration behavior
    # -------------------------------------------------------------------------

    PROXY_TIMEOUT: int = Field(
        default=30,
        description=(
            "Timeout in seconds for the underlying HTTP request to OpenAI. "
            "Applied in the OpenAI client/forwarder."
        ),
    )

    RELAY_TIMEOUT: int = Field(
        default=60,
        description=(
            "End-to-end timeout in seconds for a request as seen by the relay. "
            "Used by P4 orchestrator / middleware."
        ),
    )

    ENABLE_STREAM: bool = Field(
        default=True,
        description=(
            "If true, streaming is enabled by default where supported. "
            "Routers can still override per-request."
        ),
    )

    CHAIN_WAIT_MODE: str = Field(
        default="background",
        description=(
            "How long-running chains are handled by the orchestrator. "
            "Typical values: 'background' or 'sync' (future-proofing)."
        ),
    )

    # -------------------------------------------------------------------------
    # Relay identity and auth
    # -------------------------------------------------------------------------

    RELAY_HOST: str = Field(
        default="http://localhost:8000",
        description="Public base URL of this relay, used in logs and metadata.",
    )

    RELAY_NAME: str = Field(
        default="ChatGPT Team Relay",
        description="Human-friendly relay name (also FastAPI title).",
    )

    RELAY_AUTH_ENABLED: bool = Field(
        default=True,
        description=(
            "If true, the relay expects an auth key (X-Relay-Key or similar) "
            "for protected endpoints."
        ),
    )

    RELAY_KEY: Optional[str] = Field(
        default=None,
        description="Shared secret used by clients to authenticate with the relay.",
    )

    CHATGPT_ACTIONS_SECRET: Optional[str] = Field(
        default=None,
        description=(
            "Optional secret used to validate signatures when this relay is called "
            "as a ChatGPT Action."
        ),
    )

    # -------------------------------------------------------------------------
    # CORS configuration
    # -------------------------------------------------------------------------
    # NOTE: these are stored as CSV strings and converted into lists in main.py
    # via the `_split_csv(...)` helper.

    CORS_ALLOW_ORIGINS: str = Field(
        default="https://chat.openai.com,https://platform.openai.com",
        description="Comma-separated list of allowed origins for CORS.",
    )

    CORS_ALLOW_METHODS: str = Field(
        default="GET,POST,PUT,PATCH,DELETE,OPTIONS",
        description="Comma-separated list of allowed HTTP methods for CORS.",
    )

    CORS_ALLOW_HEADERS: str = Field(
        default="Authorization,Content-Type,Accept",
        description="Comma-separated list of allowed headers for CORS.",
    )

    # -------------------------------------------------------------------------
    # Tools & validation schema
    # -------------------------------------------------------------------------

    TOOLS_MANIFEST: str = Field(
        default="app/manifests/tools_manifest.json",
        description=(
            "Relative path (from project root) to the tools manifest JSON used "
            "by the relay / P4 orchestrator."
        ),
    )

    # IMPORTANT: the validation “schema” is a PDF API reference in this project.
    # The default matches your repo root file:
    #   ChatGPT-API_reference_ground_truth-2025-10-29.pdf
    # You can override using the VALIDATION_SCHEMA_PATH environment variable.
    VALIDATION_SCHEMA_PATH: str = Field(
        default="ChatGPT-API_reference_ground_truth-2025-10-29.pdf",
        description=(
            "Relative or absolute path to the PDF used as the ground-truth API "
            "reference / validation schema."
        ),
    )

    # -------------------------------------------------------------------------
    # Pydantic settings configuration
    # -------------------------------------------------------------------------

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Singleton settings loader.

    Using lru_cache ensures the environment is parsed once per process and
    the same Settings instance is reused across the app.
    """
    return Settings()


# Module-level singleton used throughout the app:
settings = get_settings()
