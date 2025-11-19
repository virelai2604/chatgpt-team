import logging
import os
from datetime import datetime
from typing import Any, Dict


# ---------------------------------------------------------------------------
# Environment-driven logging configuration
# ---------------------------------------------------------------------------

LOG_LEVEL = os.getenv("LOG_LEVEL", "info").upper()

# Support both:
#   - LOG_JSON=true|false  (used in .env)
#   - LOG_FORMAT=plain|json (used in render.yaml)
_log_json_raw = os.getenv("LOG_JSON")
_log_format_raw = os.getenv("LOG_FORMAT")

if _log_json_raw is not None:
    # LOG_JSON wins when explicitly set
    lowered = _log_json_raw.lower()
    if lowered in {"true", "1", "yes"}:
        LOG_FORMAT = "json"
    elif lowered in {"false", "0", "no"}:
        LOG_FORMAT = "plain"
    else:
        # Fallback to LOG_FORMAT or default
        LOG_FORMAT = (_log_format_raw or "plain").lower()
else:
    # No LOG_JSON defined → use LOG_FORMAT or default
    LOG_FORMAT = (_log_format_raw or "plain").lower()

LOG_COLOR = os.getenv("LOG_COLOR", "true").lower() == "true"

# Ensure logs directory exists (ephemeral on Render but still useful)
os.makedirs("logs", exist_ok=True)

# Log file path (ephemeral but fine for debugging)
LOG_FILE_PATH = os.path.join("logs", "relay.log")


class JsonFormatter(logging.Formatter):
    """Very small JSON-line formatter for structured logs."""

    def format(self, record: logging.LogRecord) -> str:  # type: ignore[override]
        payload: Dict[str, Any] = {
            "ts": datetime.utcfromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Optional extras that tests / operators may care about
        if record.__dict__.get("request_id"):
            payload["request_id"] = record.__dict__["request_id"]
        if record.__dict__.get("path"):
            payload["path"] = record.__dict__["path"]

        if record.exc_info:
            payload["exc_type"] = record.exc_info[0].__name__  # type: ignore[index]
        return self._to_json(payload)

    @staticmethod
    def _to_json(obj: Dict[str, Any]) -> str:
        # Minimal JSON encoding to avoid pulling in extra deps
        # We intentionally avoid orjson here to keep logger standalone.
        import json

        return json.dumps(obj, separators=(",", ":"), ensure_ascii=False)


class ColorFormatter(logging.Formatter):
    """Human-friendly colored logs for local dev."""

    COLORS = {
        "DEBUG": "\033[36m",   # Cyan
        "INFO": "\033[32m",    # Green
        "WARNING": "\033[33m", # Yellow
        "ERROR": "\033[31m",   # Red
        "CRITICAL": "\033[35m" # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:  # type: ignore[override]
        base = (
            f"[{datetime.fromtimestamp(record.created).isoformat()}] "
            f"{record.levelname:8s} {record.name}: {record.getMessage()}"
        )
        if LOG_COLOR:
            color = self.COLORS.get(record.levelname, "")
            return f"{color}{base}{self.RESET}"
        return base


def _build_formatter_for_handler(is_stream: bool) -> logging.Formatter:
    """Decide which formatter to use for a handler."""
    if LOG_FORMAT == "json":
        return JsonFormatter()
    if is_stream:
        return ColorFormatter()
    # Fallback: plain text for files
    return logging.Formatter(
        "[%(asctime)s] %(levelname)s %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )


def setup_logging() -> logging.Logger:
    """
    Initialize structured relay logging.

    Idempotent: safe to call multiple times.
    """
    root = logging.getLogger()
    # Avoid duplicating handlers in reload / tests
    if getattr(root, "_relay_logging_configured", False):
        return logging.getLogger("relay")

    root.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

    # Clear any default basicConfig handlers
    for h in list(root.handlers):
        root.removeHandler(h)

    # File handler
    file_handler = logging.FileHandler(LOG_FILE_PATH, encoding="utf-8")
    file_handler.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
    file_handler.setFormatter(_build_formatter_for_handler(is_stream=False))
    root.addHandler(file_handler)

    # Console handler (stderr)
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
    stream_handler.setFormatter(_build_formatter_for_handler(is_stream=True))
    root.addHandler(stream_handler)

    root._relay_logging_configured = True  # type: ignore[attr-defined]

    relay_logger = logging.getLogger("relay")
    relay_logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
    relay_logger.info("relay logging initialized", extra={"path": "startup"})

    return relay_logger


# Main logger instance for the relay
relay_log = setup_logging()

# Backward compatibility aliases
logger = relay_log
log = relay_log
