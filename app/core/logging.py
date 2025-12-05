"""
Logging configuration module for the ChatGPT Team Relay.

This bridges the core config with the utility logger. The main entrypoint,
`configure_logging(settings)`, ensures that the global logger is set up
exactly once using the environment-driven values (LOG_LEVEL, LOG_FORMAT, etc.)
defined in :mod:`app.utils.logger`. It accepts a ``settings`` instance but does
not mutate or rely on it; the presence of ``settings`` in the signature
satisfies FastAPI/uvicorn calling conventions.

Consumers should import and call :func:`configure_logging` at application
startup to ensure consistent logging::

    from app.core.logging import configure_logging

    configure_logging(settings)

This design keeps logging configuration centralised while allowing easy
extension in the future.
"""

from __future__ import annotations

from typing import Any

# Importing from app.utils.logger will trigger root logger configuration on
# first call. See app/utils/logger.py for environment-driven behaviour.
from app.utils.logger import get_logger


def configure_logging(settings: Any) -> None:
    """
    Initialise relay logging based on environment variables.

    This function calls into :func:`app.utils.logger.get_logger` which will
    configure the root logger exactly once using the environment variables
    ``LOG_LEVEL``, ``LOG_FORMAT``, and ``LOG_COLOR``. It accepts a
    ``settings`` parameter for interface compatibility, but does not use it
    directly.

    Args:
        settings: Pydantic settings object (unused but required for API
            compatibility).
    """
    # Ensure that the root logger is configured. The get_logger call sets up
    # formatting and levels on first invocation.
    get_logger("relay")
