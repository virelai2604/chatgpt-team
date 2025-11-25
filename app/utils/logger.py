from __future__ import annotations

import json
import logging
import os
from datetime import UTC, datetime
from typing import Any, Dict

LOG_LEVEL = os.getenv("LOG_LEVEL", "info").upper()
LOG_FORMAT = os.getenv("LOG_FORMAT", "text").lower()
LOG_COLOR = os.getenv("LOG_COLOR", "false").lower() == "true"

RELAY_NAME = os.getenv("RELAY_NAME", "ChatGPT Team Relay")
ENVIRONMENT = os.getenv("ENVIRONMENT", "local")


class JsonLogFormatter(logging.Formatter):
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

        for key, value in record.__dict__.items():
            if key not in self._RESERVED_KEYS and key not in payload:
                payload[key] = value

        return json.dumps(payload, ensure_ascii=False)


def _configure_root_logger() -> None:
    root = logging.getLogger()
    root.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

    for h in list(root.handlers):
        root.removeHandler(h)

    handler = logging.StreamHandler()

    if LOG_FORMAT == "json":
        formatter: logging.Formatter = JsonLogFormatter()
    else:
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    handler.setFormatter(formatter)
    root.addHandler(handler)


def setup_logging() -> None:
    _configure_root_logger()


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    return logger


relay_log: logging.Logger = get_logger("relay")

__all__ = ["setup_logging", "get_logger", "relay_log"]
