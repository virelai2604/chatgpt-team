# ================================================================
# logger.py — Unified Application Logger (Render-compatible)
# ================================================================
# Simple, human-readable logging utility with timestamps and colors.
# Includes setup_logger() for FastAPI / Render initialization.
# ================================================================

import sys, time, os, logging

COLORS = {
    "reset": "\033[0m",
    "green": "\033[92m",
    "yellow": "\033[93m",
    "red": "\033[91m",
    "blue": "\033[94m"
}

def log(message: str, level: str = "info"):
    """
    Prints a formatted log line to stdout with timestamp and color.
    """
    ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    color = COLORS.get("reset")
    if level == "info":
        color = COLORS["blue"]
    elif level == "warn":
        color = COLORS["yellow"]
    elif level == "error":
        color = COLORS["red"]
    elif level == "success":
        color = COLORS["green"]

    formatted = f"{color}[{ts}] [{level.upper()}] {message}{COLORS['reset']}"
    print(formatted, file=sys.stdout, flush=True)


def setup_logger():
    """
    Creates and configures a Python logging.Logger instance for Render.
    Uses environment variables for LOG_LEVEL and LOG_FORMAT.
    """
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    log_format = os.getenv("LOG_FORMAT", "text").lower()
    log_color = os.getenv("LOG_COLOR", "false").lower() == "true"

    logger = logging.getLogger("relay")

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        if log_format == "json":
            formatter = logging.Formatter(
                '{"time":"%(asctime)s","level":"%(levelname)s","message":"%(message)s"}'
            )
        else:
            color_prefix = COLORS["green"] if log_color else ""
            color_reset = COLORS["reset"] if log_color else ""
            formatter = logging.Formatter(
                f"{color_prefix}[%(asctime)s] [%(levelname)s] %(message)s{color_reset}",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(log_level)

    # Return it so app.main can use it
    return logger
