# app/routes/usage.py
# BIFL v2.2 — Unified Usage and Analytics Endpoint
# Tracks token usage, latency, and response statistics across all relay operations.

import os
import time
import sqlite3
from fastapi import APIRouter, HTTPException, Query
from app.api.forward import forward_openai
from typing import Dict, Any, List, Optional

router = APIRouter(prefix="/v1/usage", tags=["Usage"])

# === Configuration ===
USAGE_DIR = os.getenv("USAGE_DIR", "data/usage")
DB_PATH = os.path.join(USAGE_DIR, "usage.db")
os.makedirs(USAGE_DIR, exist_ok=True)

# === Database Init ===
def init_db():
    with sqlite3.connect(DB_PATH) as db:
        db.execute("""
        CREATE TABLE IF NOT EXISTS usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model TEXT,
            input_tokens INTEGER,
            output_tokens INTEGER,
            total_tokens INTEGER,
            latency_ms REAL,
            user_id TEXT,
            session_id TEXT,
            created_at INTEGER
        );
        """)
init_db()


def record_usage(model: str, input_tokens: int, output_tokens: int, latency_ms: float, user_id: str = "anon", session_id: str = "default"):
    with sqlite3.connect(DB_PATH) as db:
        total = input_tokens + output_tokens
        db.execute(
            "INSERT INTO usage (model, input_tokens, output_tokens, total_tokens, latency_ms, user_id, session_id, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (model, input_tokens, output_tokens, total, latency_ms, user_id, session_id, int(time.time())),
        )
        db.commit()


def query_usage(limit: int = 50) -> List[Dict[str, Any]]:
    with sqlite3.connect(DB_PATH) as db:
        rows = db.execute(
            "SELECT model, input_tokens, output_tokens, total_tokens, latency_ms, user_id, session_id, created_at FROM usage ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [
            {
                "model": r[0],
                "input_tokens": r[1],
                "output_tokens": r[2],
                "total_tokens": r[3],
                "latency_ms": r[4],
                "user_id": r[5],
                "session_id": r[6],
                "created_at": r[7],
            }
            for r in rows
        ]


def summarize_usage(period: Optional[str] = None) -> Dict[str, Any]:
    """Summarize usage totals optionally by period (day/week/all)."""
    with sqlite3.connect(DB_PATH) as db:
        if period == "day":
            start = int(time.time()) - 86400
            rows = db.execute("SELECT SUM(total_tokens), COUNT(*) FROM usage WHERE created_at >= ?", (start,)).fetchone()
        elif period == "week":
            start = int(time.time()) - 7 * 86400
            rows = db.execute("SELECT SUM(total_tokens), COUNT(*) FROM usage WHERE created_at >= ?", (start,)).fetchone()
        else:
            rows = db.execute("SELECT SUM(total_tokens), COUNT(*) FROM usage").fetchone()
    total_tokens, calls = rows or (0, 0)
    return {"total_tokens": total_tokens or 0, "calls": calls or 0, "period": period or "all"}


# === Routes ===

@router.get("/")
async def list_usage(limit: int = Query(50, description="Number of recent entries to fetch")):
    """List recent usage records."""
    data = query_usage(limit)
    return JSONResponse(content={"object": "list", "data": data})


@router.get("/summary")
async def usage_summary(period: Optional[str] = Query(None, description="Optional: day, week, all")):
    """Get summarized token usage totals."""
    summary = summarize_usage(period)
    return JSONResponse(content={"object": "usage_summary", "data": summary})


@router.post("/record")
async def add_usage_record(body: Dict[str, Any]):
    """Manually record a usage entry (for external tools)."""
    try:
        model = body.get("model", "unknown")
        input_tokens = int(body.get("input_tokens", 0))
        output_tokens = int(body.get("output_tokens", 0))
        latency_ms = float(body.get("latency_ms", 0))
        user_id = body.get("user_id", "anon")
        session_id = body.get("session_id", "default")
        record_usage(model, input_tokens, output_tokens, latency_ms, user_id, session_id)
        return JSONResponse(content={"status": "ok", "message": "usage recorded"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record usage: {e}")


@router.get("/models")
async def model_usage():
    """Aggregate usage by model."""
    with sqlite3.connect(DB_PATH) as db:
        rows = db.execute("""
        SELECT model, COUNT(*), SUM(total_tokens), ROUND(AVG(latency_ms), 2)
        FROM usage GROUP BY model ORDER BY SUM(total_tokens) DESC
        """).fetchall()
        data = [
            {
                "model": r[0],
                "calls": r[1],
                "total_tokens": r[2],
                "avg_latency_ms": r[3],
            }
            for r in rows
        ]
    return JSONResponse(content={"object": "usage_by_model", "data": data})


@router.get("/ping")
async def usage_ping():
    """Quick usage service health check."""
    return JSONResponse(content={"object": "usage", "ok": True, "version": "v2.2", "timestamp": int(time.time())})
