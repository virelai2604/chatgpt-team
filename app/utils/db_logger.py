# ==========================================================
# app/utils/db_logger.py — Unified Database Logger
# ==========================================================
import os
import sqlite3
import logging
from pathlib import Path
from datetime import datetime

def setup_logging(db_path: str):
    """
    Initializes SQLite logging and a .log file.
    Ensures schema creation and log persistence.
    """
    Path(os.path.dirname(db_path)).mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=str(Path(db_path).with_suffix(".log")),
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    logging.info(f"[DBLogger] Using database at: {db_path}")
    return db_path


def ensure_schema(db_path: str):
    """
    Creates tables for relay event logging if not present.
    Schema includes generic fields for Requests, Responses, and Tools.
    """
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS relay_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        route TEXT NOT NULL,
        status_code INTEGER,
        message TEXT,
        model TEXT,
        duration_ms REAL DEFAULT 0
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS tool_calls (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        tool_name TEXT,
        payload TEXT,
        result TEXT
    )
    """)

    conn.commit()
    conn.close()


def log_event(route: str, status_code: int, message: str, model: str = None, duration_ms: float = 0.0):
    """
    Logs a single API or tool call into the database and log file.
    """
    db_path = os.getenv("BIFL_DB_PATH", "/data/chatgpt_archive.sqlite")
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO relay_logs (timestamp, route, status_code, message, model, duration_ms) VALUES (?, ?, ?, ?, ?, ?)",
            (datetime.utcnow().isoformat() + "Z", route, status_code, message, model, duration_ms)
        )
        conn.commit()
        conn.close()
        logging.info(f"[RelayLog] {route} ({status_code}) — {message}")
    except Exception as e:
        logging.error(f"[DBLogger] Failed to log event: {e}")
