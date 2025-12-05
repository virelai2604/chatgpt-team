# app/utils/logger.py

from __future__ import annotations

import logging
import os
from typing import Optional

_LOGGER_ROOT_NAME = "chatgpt_team_relay"


def configure_logging(level: Optional[str] = None) -> None:
    """
    Configure the root relay logger.

    Idempotent: calling it multiple times will not duplicate handlers.
    """
    logger = logging.getLogger(_LOGGER_ROOT_NAME)
    if logger.handlers:
        # Already configured
        return

    level_name = level or os.getenv("LOG_LEVEL", "INFO")
    log_level = getattr(logging, level_name.upper(), logging.INFO)

    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)

    logger.setLevel(log_level)
    logger.addHandler(handler)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a child logger under the relay root.

    Example:
        logger = get_logger(__name__)
    """
    configure_logging()

    if not name:
        return logging.getLogger(_LOGGER_ROOT_NAME)

    return logging.getLogger(f"{_LOGGER_ROOT_NAME}.{name}")


# Shared relay logger used by routes: `from app.utils.logger import relay_log as logger`
relay_log = get_logger("relay")
