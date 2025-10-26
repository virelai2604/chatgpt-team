# app/utils/db_logger.py — BIFL v2.3.3
import sqlite3, os, asyncio
from datetime import datetime

DB_PATH = os.getenv("BIFL_DB_PATH", r"D:\ChatgptDATAB\DB Chatgpt\chatgpt_archive.sqlite")
_log_queue: asyncio.Queue = asyncio.Queue()

async def _writer():
    """Background async writer for queued DB inserts."""
    while True:
        try:
            func, args = await _log_queue.get()
            func(*args)
        except Exception as e:
            print(f"[DB_LOGGER] Error: {e}")
        finally:
            _log_queue.task_done()

def _connect():
    return sqlite3.connect(DB_PATH)

def save_raw_request(endpoint, raw_body, headers_json, relay_version="2.3.3"):
    with _connect() as conn:
        conn.execute(
            "INSERT INTO raw_requests (timestamp, endpoint, body, headers_json, relay_version) VALUES (?, ?, ?, ?, ?)",
            (datetime.now().isoformat(), endpoint, raw_body, headers_json, relay_version)
        )

def init_db():
    """Ensure tables exist with new columns."""
    with _connect() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS raw_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            endpoint TEXT,
            body BLOB,
            headers_json TEXT,
            relay_version TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_raw_endpoint ON raw_requests(endpoint);
        """)
    print("[BIFL] SQLite database initialized.")

async def init_async_writer():
    asyncio.create_task(_writer())
    print("[BIFL] Async DB writer started.")
