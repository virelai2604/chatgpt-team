import logging
import os
from datetime import datetime


# Ensure logs directory exists
os.makedirs("logs", exist_ok=True)

# Create a timestamped log file
log_file = os.path.join("logs", "relay.log")

# Basic logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)

# Main logger instance
relay_log = logging.getLogger("relay")
relay_log.setLevel(logging.INFO)


def setup_logging():
    """Initialize structured relay logging."""
    relay_log.info(f"📜 Logging initialized at {datetime.now()} → {log_file}")


# For backward compatibility
logger = relay_log
log = relay_log
