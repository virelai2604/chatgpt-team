from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional

# ---------------------------------------------------------------------------
# Environment configuration
# ---------------------------------------------------------------------------

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FORMAT = os.getenv("LOG_FORMAT", "structured").lower()  # "structured" or "plain"
LOG_COLOR = os.getenv("LOG_COLOR", "false").lower() == "true"
ENVIRONMENT = os.getenv("ENVIRONMENT", os.getenv("APP_MODE", "local"))


# ---------------------------------------------------------------------------
# JSON formatter for relay logs
# ---------------------------------------------------------------------------

class JsonFormatter(logging.Formatter):
    """
    Minimal JSON formatter to match the relay-style logs you see like:

      {"ts":"2025-11-20T00:38:09.440496Z",
       "level":"INFO",
       "logger":"relay",
       "message":"relay logging initialized",
       "path":"startup",
       "environment":"production"}
    """

    def format(self, record: logging.LogRecord) -> str:
        # Base payload
        payload: Dict[str, Any] = {
            "ts": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat().replace("+00:00", "Z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "environment": ENVIRONMENT,
        }

        # Optionally include a "path" field if the record has it
        if hasattr(record, "path"):
            payload["path"] = getattr(record, "path")

        # Include exception info if present
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Handler + setup helpers
# ---------------------------------------------------------------------------

def _build_handler() -> logging.Handler:
    """
    Build a stdout handler using either JSON or plain formatting.
    """
    handler = logging.StreamHandler(sys.stdout)

    if LOG_FORMAT in ("structured", "json"):
        formatter: logging.Formatter = JsonFormatter()
    else:
        # Simple plain-text fallback if you ever change LOG_FORMAT
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S%z",
        )

    handler.setFormatter(formatter)
    return handler


def setup_logging() -> logging.Logger:
    """
    Configure root logging once, and return the main relay logger.

    Used by app.main at startup.
    """
    root = logging.getLogger()

    # If already configured, just return the relay logger
    if root.handlers:
        return logging.getLogger("relay")

    # Configure root logger
    root.setLevel(LOG_LEVEL)

    handler = _build_handler()
    root.addHandler(handler)

    # Ensure our primary named logger exists
    relay_logger = logging.getLogger("relay")
    relay_logger.setLevel(LOG_LEVEL)

    return relay_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a named logger, ensuring logging is initialized first.

    Used by forwarders and routes:
      from app.utils.logger import get_logger
      log = get_logger("relay.orchestrator")
    """
    # If no handlers yet, initialize logging (safe to call multiple times)
    if not logging.getLogger().handlers:
        setup_logging()
    return logging.getLogger(name)


# ---------------------------------------------------------------------------
# Default relay logger alias
# ---------------------------------------------------------------------------

# This is what conversations.py expects:
#   from app.utils.logger import relay_log as log
relay_log: logging.Logger = get_logger("relay")
