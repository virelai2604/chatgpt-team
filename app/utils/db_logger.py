# ============================================================
# app/utils/db_logger.py — BIFL Database & Logging Utility
# Version: 2.3.4-fp
# ============================================================

import os
import json
import logging
from datetime import datetime
from typing import Any, Dict

logger = logging.getLogger("BIFL.DBLogger")

# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------
LOG_DIR = os.getenv("BIFL_LOG_DIR", "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# ------------------------------------------------------------
# 🧩 init_db — Initialize logging/DB layer (async-safe)
# ------------------------------------------------------------
async def init_db():
    """Initialize the database or file-based logging directory (async-safe)."""
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        logger.info(f"[DBLogger] Initialized log directory at: {LOG_DIR}")
        return True
    except Exception as e:
        logger.error(f"[DBLogger] Failed to initialize DB logger: {e}")
        return False

# ------------------------------------------------------------
# 💾 save_raw_request — Log raw request payloads for observability
# ------------------------------------------------------------
async def save_raw_request(endpoint: str, body: Dict[str, Any]):
    """Save raw API request body as a local JSON file for debugging/auditing."""
    try:
        timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%SZ")
        filename = os.path.join(LOG_DIR, f"{endpoint}_{timestamp}.json")
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(body, f, indent=2)
        logger.info(f"[DBLogger] Saved raw request: {filename}")
    except Exception as e:
        logger.warning(f"[DBLogger] Failed to log request: {e}")

# ------------------------------------------------------------
# 🧾 log_event — Append brief relay activity log
# ------------------------------------------------------------
async def log_event(endpoint: str, status_code: int, message: str):
    """Record a brief event log entry."""
    try:
        timestamp = datetime.utcnow().isoformat()
        filename = os.path.join(LOG_DIR, "relay_events.log")
        with open(filename, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {endpoint} ({status_code}) - {message}\n")
    except Exception as e:
        logger.warning(f"[DBLogger] Failed to log event: {e}")
