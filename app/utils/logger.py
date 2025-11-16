import logging
import os
from datetime import datetime

# Read log level from environment (default: INFO)
LOG_LEVEL = os.getenv("LOG_LEVEL", "info").upper()

# Ensure logs directory exists (ephemeral on Render but still useful)
os.makedirs("logs", exist_ok=True)

# Log file path (ephemeral but fine for debugging)
log_file = os.path.join("logs", "relay.log")

# Basic logging configuration
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding="utf-8"),
        logging.StreamHandler(),  # console/stdout (Render captures this)
    ],
)

# Main logger instance for the relay
relay_log = logging.getLogger("relay")
relay_log.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))


def setup_logging():
    """Initialize structured relay logging."""
    relay_log.info(f"📜 Logging initialized at {datetime.now()} → {log_file}")


# Backward compatibility aliases
logger = relay_log
log = relay_log
