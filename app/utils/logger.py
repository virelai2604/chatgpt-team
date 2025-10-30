# ==========================================================
# app/utils/logger.py — simple shared logger
# ==========================================================
import logging

# Configure once if not already set
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
)

# Export a helper function compatible with legacy calls
def log(message: str, level: str = "info"):
    """Legacy logger shim for backward compatibility."""
    logger = logging.getLogger("chatgpt-team-relay")
    if level == "error":
        logger.error(message)
    elif level == "warn" or level == "warning":
        logger.warning(message)
    elif level == "debug":
        logger.debug(message)
    else:
        logger.info(message)
