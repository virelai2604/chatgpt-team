# app/utils/db_logger.py — BIFL v2.3.4-fp
import os, aiosqlite, asyncio

DB_PATH = os.getenv("BIFL_DB_PATH", "/data/chatgpt_archive.sqlite")

async def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS relay_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                route TEXT,
                status INTEGER,
                message TEXT
            )
        """)
        await db.commit()

async def log_event(route: str, status: int, message: str):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT INTO relay_logs (route, status, message) VALUES (?,?,?)",
                (route, status, message)
            )
            await db.commit()
    except Exception:
        pass  # non-critical
