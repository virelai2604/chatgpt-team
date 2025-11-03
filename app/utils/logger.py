# app/utils/logger.py
from rich.console import Console
from rich.theme import Theme
import logging

_custom_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "bold red",
    "success": "green"
})

console = Console(theme=_custom_theme)


def setup_logger(name: str = "relay"):
    """Initialize and return a colorized logger using Rich + standard logging."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s — %(message)s", "%H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    # Also show a banner at startup
    console.print("🪶 Logger initialized — Rich console active.", style="success")
    return logger


# Global instance used by middleware and startup events
log = setup_logger("app")

def info(message: str):
    console.print(f"[INFO] {message}", style="info")
    log.info(message)

def warn(message: str):
    console.print(f"[WARN] {message}", style="warning")
    log.warning(message)

def error(message: str):
    console.print(f"[ERROR] {message}", style="error")
    log.error(message)
