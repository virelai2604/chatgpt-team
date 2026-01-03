from __future__ import annotations

import logging
import os
import sys
from typing import Any, Optional
from logging.handlers import RotatingFileHandler

_LOGGER_ROOT_NAME = "chatgpt_team_relay"


def _coerce_log_level(value: Any) -> int:
    """
    Convert arbitrary env/config values into a valid logging level integer.

    Why:
      - Render env vars are always strings; misconfig like LOG_LEVEL=FALSE
        will crash logging.setLevel("FALSE") with ValueError.
      - We harden to avoid taking the whole service down due to config typos.

    Accepts:
      - int levels (e.g. 20)
      - standard names (DEBUG/INFO/WARNING/ERROR/CRITICAL)
      - common aliases (WARN, FATAL)
      - "true/false" -> fallback to INFO
    """
    if isinstance(value, int) and not isinstance(value, bool):
        return value

    if isinstance(value, bool):
        # Treat booleans as "use default verbosity" rather than crashing.
        return logging.INFO

    s = str(value or "").strip()
    if not s:
        return logging.INFO

    s_upper = s.upper()

    # Common misconfigs where someone thought this was a boolean toggle.
    if s_upper in {"TRUE", "FALSE"}:
        return logging.INFO

    # Numeric strings
    if s_upper.isdigit():
        try:
            return int(s_upper)
        except Exception:
            return logging.INFO

    # Common aliases
    if s_upper == "WARN":
        s_upper = "WARNING"
    elif s_upper == "FATAL":
        s_upper = "CRITICAL"

    # Official mapping (Py 3.11+)
    mapping = logging.getLevelNamesMapping()
    if s_upper in mapping:
        return int(mapping[s_upper])

    return logging.INFO


def configure_logging(level: Optional[str] = None) -> None:
    """Idempotent logging setup for local dev and production.

    - Uses a single StreamHandler to stdout
    - Avoids duplicate handlers on reload
    - Sets a clean, grep-friendly format
    """
    resolved_level = _coerce_log_level(level or os.getenv("LOG_LEVEL") or "INFO")

    root_logger = logging.getLogger(_LOGGER_ROOT_NAME)

    # Idempotency: don't stack handlers on reload.
    if getattr(root_logger, "_relay_configured", False):
        root_logger.setLevel(resolved_level)
        for h in list(root_logger.handlers):
            h.setLevel(resolved_level)
        return

    root_logger.setLevel(resolved_level)
    root_logger.propagate = False

    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setLevel(resolved_level)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )

    root_logger.addHandler(handler)

    error_log_path = os.getenv("ERROR_LOG_PATH", "data/logs/errors.log").strip()
    if error_log_path:
        error_log_dir = os.path.dirname(error_log_path)
        if error_log_dir:
            os.makedirs(error_log_dir, exist_ok=True)
        try:
            with open(error_log_path, "a", encoding="utf-8"):
                pass
        except OSError:
            error_log_path = ""

    if error_log_path:
        error_handler = RotatingFileHandler(
            error_log_path,
            maxBytes=int(os.getenv("ERROR_LOG_MAX_BYTES", str(5 * 1024 * 1024))),
            backupCount=int(os.getenv("ERROR_LOG_BACKUP_COUNT", "5")),
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        root_logger.addHandler(error_handler)

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
