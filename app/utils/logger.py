# app/utils/logger.py

from __future__ import annotations

import logging
import sys
from typing import Optional


_LOGGER_CONFIGURED = False


def configure_logging(level: str = "INFO") -> None:
    """
    Configure root logging once, in a simple JSON-ish console format.

    Called from app/main.py with the level coming from Settings.
    """
    global _LOGGER_CONFIGURED
    if _LOGGER_CONFIGURED:
        return

    logging.basicConfig(
        level=level.upper(),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        stream=sys.stdout,
    )
    _LOGGER_CONFIGURED = True


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Small wrapper around logging.getLogger so we only have a single
    configuration surface.
    """
    return logging.getLogger(name if name else __name__)
