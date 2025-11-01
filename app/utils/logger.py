# ==========================================================
# app/utils/logger.py — Ground Truth Structured Logger
# ==========================================================
"""
Unified structured logging for ChatGPT Team Relay.
Implements JSON-formatted, environment-aware logging consistent with
OpenAI SDK and Ground Truth API v1.7 behavior.
"""

import os
import sys
import json
import logging
from datetime import datetime

# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FORMAT = os.getenv("LOG_FORMAT", "json").lower()
LOG_FILE = os.getenv("LOG_FILE", "").strip()
ENABLE_COLOR = os.getenv("LOG_COLOR", "true").lower() == "true"


# --------------------------------------------------------------------------
# JSON Formatter
# --------------------------------------------------------------------------

class JSONFormatter(logging.Formatter):
    """Format logs as structured JSON for ingestion or Cloud logs."""

    def format(self, record):
        log_record = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "module": record.module,
            "message": record.getMessage(),
        }

        if hasattr(record, "extra") and isinstance(record.extra, dict):
            log_record.update(record.extra)

        if record.exc_info:
            log_record["error"] = self.formatException(record.exc_info)

        return json.dumps(log_record, ensure_ascii=False)


# --------------------------------------------------------------------------
# Color Text Formatter (for local dev)
# --------------------------------------------------------------------------

class ColorFormatter(logging.Formatter):
    """Simple colorized console formatter for local use."""

    COLORS = {
        "DEBUG": "\033[36m",   # Cyan
        "INFO": "\033[32m",    # Green
        "WARNING": "\033[33m", # Yellow
        "ERROR": "\033[31m",   # Red
        "CRITICAL": "\033[41m" # Red background
    }

    def format(self, record):
        color = self.COLORS.get(record.levelname, "")
        reset = "\033[0m"
        ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        return f"{color}[{ts}] {record.levelname:<8} {record.module}: {record.getMessage()}{reset}"


# --------------------------------------------------------------------------
# Logger Setup
# --------------------------------------------------------------------------

logger = logging.getLogger("relay")
logger.setLevel(LOG_LEVEL)
logger.propagate = False

# Remove duplicate handlers (if reloaded)
for h in list(logger.handlers):
    logger.removeHandler(h)

handler = logging.StreamHandler(sys.stdout)

if LOG_FORMAT == "json":
    formatter = JSONFormatter()
else:
    formatter = ColorFormatter() if ENABLE_COLOR else logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

handler.setFormatter(formatter)
logger.addHandler(handler)

# Optional file logging
if LOG_FILE:
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setFormatter(JSONFormatter() if LOG_FORMAT == "json" else ColorFormatter())
    logger.addHandler(file_handler)

# --------------------------------------------------------------------------
# Helper Functions
# --------------------------------------------------------------------------

def set_level(level: str):
    """Dynamically change log level at runtime."""
    logger.setLevel(level.upper())
    logger.info(f"Log level changed to {level.upper()}")


def log_startup_banner(version: str):
    """Print a banner on startup with context info."""
    banner = {
        "event": "startup",
        "version": version,
        "environment": os.getenv("ENV", "development"),
        "passthrough": os.getenv("DISABLE_PASSTHROUGH", "false"),
        "sdk_target": "openai-python 2.6.1",
    }
    logger.info(json.dumps(banner))
