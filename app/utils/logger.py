from __future__ import annotations

import logging
import os
from typing import Optional

_LOGGER_ROOT_NAME = "chatgpt_team_relay"


def configure_logging(level: Optional[str] = None) -> None:
    """Idempotent logging setup for local dev and production.

    - Uses a single StreamHandler to stdout
    - Avoids duplicate handlers on reload
    - Sets a clean, grep-friendly format
    """
    resolved_level = (level or os.getenv("LOG_LEVEL") or "INFO").upper()
    root_logger = logging.getLogger(_LOGGER_ROOT_NAME)

    # Idempotency: don't stack handlers on reload.
    if getattr(root_logger, "_relay_configured", False):
        root_logger.setLevel(resolved_level)
        return

    root_logger.setLevel(resolved_level)
    root_logger.propagate = False

    handler = logging.StreamHandler()
    handler.setLevel(resolved_level)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )

    root_logger.addHandler(handler)
    setattr(root_logger, "_relay_configured", True)


def get_logger(name: str) -> logging.Logger:
    """Return a namespaced logger under the relay root."""
    if not name:
        return logging.getLogger(_LOGGER_ROOT_NAME)
    return logging.getLogger(f"{_LOGGER_ROOT_NAME}.{name}")


# Default logger used across the codebase.
relay_log = get_logger("relay")


# ---------------------------------------------------------------------------
# Backward-compatible convenience functions.
# Some older route modules imported these directly (e.g., `from app.utils.logger import info`).
# ---------------------------------------------------------------------------

def debug(msg: str, *args, **kwargs) -> None:
    relay_log.debug(msg, *args, **kwargs)


def info(msg: str, *args, **kwargs) -> None:
    relay_log.info(msg, *args, **kwargs)


def warning(msg: str, *args, **kwargs) -> None:
    relay_log.warning(msg, *args, **kwargs)


# Common alias
warn = warning


def error(msg: str, *args, **kwargs) -> None:
    relay_log.error(msg, *args, **kwargs)


def exception(msg: str, *args, **kwargs) -> None:
    relay_log.exception(msg, *args, **kwargs)
