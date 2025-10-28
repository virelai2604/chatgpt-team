import logging
import sqlite3
import os

def setup_logging():
    """Initialize unified file + SQLite logging."""
    db_path = os.getenv("BIFL_DB_PATH", "logs/relay_logs.sqlite")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    # Create table if missing
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT DEFAULT (datetime('now')),
            level TEXT,
            message TEXT
        );
    """)
    conn.commit()
    conn.close()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[logging.StreamHandler()]
    )

    class SQLiteHandler(logging.Handler):
        """Custom logging handler that writes to SQLite."""
        def emit(self, record):
            try:
                conn = sqlite3.connect(db_path)
                conn.execute(
                    "INSERT INTO logs (level, message) VALUES (?, ?)",
                    (record.levelname, record.getMessage())
                )
                conn.commit()
                conn.close()
            except Exception as e:
                print(f"Logging error: {e}")

    logging.getLogger().addHandler(SQLiteHandler())


def log_event(level: str, message: str):
    """Manual helper for API-level event logging."""
    logging.log(getattr(logging, level.upper(), logging.INFO), message)
