import json
import logging
import os
from datetime import UTC, datetime
from typing import Any, Dict

# -----------------------------------------------------------------------------
# Environment-driven configuration
# -----------------------------------------------------------------------------

LOG_LEVEL = os.getenv("LOG_LEVEL", "info").upper()
LOG_FORMAT = os.getenv("LOG_FORMAT", "text").lower()  # "json" or "text"
LOG_COLOR = os.getenv("LOG_COLOR", "false").lower() == "true"

RELAY_NAME = os.getenv("RELAY_NAME", "ChatGPT Team Relay")
ENVIRONMENT = os.getenv("ENVIRONMENT", "local")


# -----------------------------------------------------------------------------
# JSON formatter
# -----------------------------------------------------------------------------

class JsonLogFormatter(logging.Formatter):
    """
    JSON formatter used by the relay.

    Produces log lines like:
    {
      "ts": "2025-11-20T00:38:09.440496Z",
      "level": "INFO",
      "logger": "relay",
      "message": "relay logging initialized",
      "environment": "production",
      "path": "startup",
      ...
    }
    """

    # Standard logging attributes to exclude from "extra" expansion
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
        # Modern, timezone-aware timestamp, then normalized to "Z"
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

        # Attach exception info if present
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)

        # Merge any extra attributes that the app attaches to the record
        for key, value in record.__dict__.items():
            if key not in self._RESERVED_KEYS and key not in payload:
                payload[key] = value

        return json.dumps(payload, ensure_ascii=False)


# -----------------------------------------------------------------------------
# Logger setup helpers
# -----------------------------------------------------------------------------

def _configure_root_logger() -> None:
    """Configure the root logger according to env vars."""
    root = logging.getLogger()
    root.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

    # Clear existing handlers so pytest / uvicorn reloads don't duplicate them
    for h in list(root.handlers):
        root.removeHandler(h)

    handler = logging.StreamHandler()

    if LOG_FORMAT == "json":
        formatter: logging.Formatter = JsonLogFormatter()
    else:
        # Simple human-readable format
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    handler.setFormatter(formatter)
    root.addHandler(handler)


def setup_logging() -> None:
    """
    Public entrypoint used by app.main.

    Safe to call multiple times; it will reconfigure the root logger cleanly.
    """
    _configure_root_logger()


def get_logger(name: str) -> logging.Logger:
    """
    Get a namespaced logger. Modules should use this instead of logging.getLogger directly
    so that they follow the relay’s configuration.
    """
    logger = logging.getLogger(name)
    # Do not add handlers here – rely on the root logger configuration.
    return logger


# Convenience logger used by several modules (e.g., orchestrator, startup)
relay_log: logging.Logger = get_logger("relay")


__all__ = ["setup_logging", "get_logger", "relay_log"]
