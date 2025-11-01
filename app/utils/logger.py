# ================================================================
# logger.py — Unified Application Logger
# ================================================================
# Simple, human-readable logging utility with timestamps and colors.
# This logger is safe for async contexts and Cloudflare / GCP logs.
# ================================================================

import sys, time

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
