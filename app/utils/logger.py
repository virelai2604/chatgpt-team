from __future__ import annotations

import json
import logging
import os
import sys
from datetime import UTC, datetime
from typing import Any, Dict


# ---------------------------------------------------------------------------
# Environment-driven logging configuration
# ---------------------------------------------------------------------------

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FORMAT = os.getenv("LOG_FORMAT", "text").lower()  # "text" | "json"
LOG_COLOR = os.getenv("LOG_COLOR", "false").lower() == "true"

RELAY_NAME = os.getenv("RELAY_NAME", "ChatGPT Team Relay")
ENVIRONMENT = os.getenv("ENVIRONMENT", "local")


# ---------------------------------------------------------------------------
# JSON formatter
# ---------------------------------------------------------------------------


class JsonLogFormatter(logging.Formatter):
    """
    JSON log formatter used when LOG_FORMAT=json.

    Produces structured payloads such as:
      {
        "ts": "...",
        "level": "INFO",
        "logger": "relay",
        "message": "something happened",
        "environment": "local",
        "relay": "ChatGPT Team Relay",
        "extra_field": "value"
      }
    """

    _RESERVED_KEYS = {
        "name",
        "msg",
        "args",
        "levelname",
        "levelno",
        "pathname",
        "filename",
        "module",
        "exc_info",
        "exc_text",
        "stack_info",
        "lineno",
        "funcName",
        "created",
        "msecs",
        "relativeCreated",
        "thread",
        "threadName",
        "processName",
        "process",
        "asctime",
    }

    def format(self, record: logging.LogRecord) -> str:  # type: ignore[override]
        ts = (
            datetime.fromtimestamp(record.created, UTC)
            .isoformat()
            .replace("+00:00", "Z")
        )

        payload: Dict[str, Any] = {
            "ts": ts,
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "environment": ENVIRONMENT,
            "relay": RELAY_NAME,
        }

        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)

        # Add any user-defined extra fields that aren't reserved
        for key, value in record.__dict__.items():
            if key not in self._RESERVED_KEYS and key not in payload:
                payload[key] = value

        return json.dumps(payload, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Root logger configuration
# ---------------------------------------------------------------------------

_configured = False


def _configure_root_logger() -> None:
    """
    Configure the root logger exactly once, based on environment variables.

    This is intentionally simple:
      - Single StreamHandler to stdout
      - JSON or text formatter
      - Level from LOG_LEVEL
    """
    global _configured
    if _configured:
        return

    root = logging.getLogger()
    # If something already configured handlers (e.g., uvicorn),
    # we respect that and just adjust levels/format where reasonable.
    if not root.handlers:
        handler = logging.StreamHandler(stream=sys.stdout)

        if LOG_FORMAT == "json":
            formatter: logging.Formatter = JsonLogFormatter()
        else:
            # Simple human-readable format. Coloring is optional and
            # left minimal to avoid coupling to external libraries.
            if LOG_COLOR:
                # Basic ANSI coloring by level
                fmt = "%(levelname)s %(name)s - %(message)s"
            else:
                fmt = "%(asctime)s %(levelname)s [%(name)s] %(message)s"

            formatter = logging.Formatter(fmt)

        handler.setFormatter(formatter)
        root.addHandler(handler)

    # Set level on the root logger
    try:
        level = getattr(logging, LOG_LEVEL, logging.INFO)
    except Exception:
        level = logging.INFO
    root.setLevel(level)

    _configured = True


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------


def get_logger(name: str) -> logging.Logger:
    """
    Return a logger with the relay's standard configuration.

    Usage:
        from app.utils.logger import get_logger
        logger = get_logger("my_module")
    """
    _configure_root_logger()
    return logging.getLogger(name)


# Canonical relay logger used across the project
relay_log = get_logger("relay")

__all__ = ["get_logger", "relay_log", "JsonLogFormatter"]
