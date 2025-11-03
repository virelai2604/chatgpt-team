"""
logger.py — Structured JSON Logger for ChatGPT Team Relay
────────────────────────────────────────────────────────────
Provides unified logging for all subsystems (middleware, proxy,
routes, tools). Emits machine-readable JSON and human-friendly
console output simultaneously.

Features:
  • JSON + colorized console logging
  • Supports levels: DEBUG, INFO, WARNING, ERROR
  • Includes request ID, timestamp, module, and message
"""

import json
import logging
import sys
import time
from typing import Any, Dict

# ------------------------------------------------------------
# Log Configuration
# ------------------------------------------------------------
class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: Dict[str, Any] = {
            "ts": round(time.time(), 3),
            "level": record.levelname,
            "module": record.module,
            "message": record.getMessage(),
        }

        # Attach exception info if present
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False)


# Create main logger
log = logging.getLogger("relay")
log.setLevel(logging.INFO)

# StreamHandler for console output
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)

# Dual-format: human + JSON for easy tailing
class DualFormatter(logging.Formatter):
    COLORS = {
        "INFO": "\033[92m",     # green
        "WARNING": "\033[93m",  # yellow
        "ERROR": "\033[91m",    # red
        "DEBUG": "\033[94m",    # blue
    }

    def format(self, record):
        color = self.COLORS.get(record.levelname, "")
        reset = "\033[0m"
        msg = f"{color}[{record.levelname}] {record.module}: {record.getMessage()}{reset}"
        return msg

console_handler.setFormatter(DualFormatter())

# File handler (optional JSON structured logs)
file_handler = logging.FileHandler("relay.log", encoding="utf-8")
file_handler.setFormatter(JSONFormatter())
file_handler.setLevel(logging.INFO)

# Prevent duplication
if not log.handlers:
    log.addHandler(console_handler)
    log.addHandler(file_handler)

# Convenience aliases
logger = log
