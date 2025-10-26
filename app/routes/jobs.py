# app/routes/jobs.py
# BIFL v2.2 — Unified Background Job Manager
# Handles creation, listing, cancellation, and progress tracking for long-running tasks.

import os
import time
import uuid
import sqlite3
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Body
from fastapi.responses import JSONResponse
from app.api.forward import forward_openai


router = APIRouter(prefix="/v1/jobs", tags=["Jobs"])

JOBS_DIR = os.getenv("JOBS_DIR", "data/jobs")
DB_PATH = os.path.join(JOBS_DIR, "jobs.db")
os.makedirs(JOBS_DIR, exist_ok=True)


# === Init Database ===
def init_db():
    with sqlite3.connect(DB_PATH) as db:
        db.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            type TEXT,
            status TEXT,
            created_at INTEGER,
            updated_at INTEGER,
            params TEXT,
            result TEXT
        );
        """)
init_db()


# === Core Helpers ===
def create_job_record(job_type: str, params: Dict[str, Any]) -> str:
    job_id = str(uuid.uuid4())
    now = int(time.time())
    with sqlite3.connect(DB_PATH) as db:
        db.execute(
            "INSERT INTO jobs (id, type, status, created_at, updated_at, params, result) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (job_id, job_type, "queued", now, now, str(params), "{}"),
        )
        db.commit()
    return job_id


def update_job_status(job_id: str, status: str, result: Dict[str, Any] = None):
    now = int(time.time())
    with sqlite3.connect(DB_PATH) as db:
        db.execute(
            "UPDATE jobs SET status=?, updated_at=?, result=? WHERE id=?",
            (status, now, str(result or {}), job_id),
        )
        db.commit()


def get_job(job_id: str):
    with sqlite3.connect(DB_PATH) as db:
        row = db.execute(
            "SELECT id, type, status, created_at, updated_at, params, result FROM jobs WHERE id=?",
            (job_id,)
        ).fetchone()
    if not row:
        return None
    return {
        "id": row[0],
        "type": row[1],
        "status": row[2],
        "created_at": row[3],
        "updated_at": row[4],
        "params": row[5],
        "result": row[6],
    }


def list_jobs(limit: int = 50):
    with sqlite3.connect(DB_PATH) as db:
        rows = db.execute(
            "SELECT id, type, status, created_at, updated_at FROM jobs ORDER BY created_at DESC LIMIT ?",
            (limit,)
        ).fetchall()
    return [
        {"id": r[0], "type": r[1], "status": r[2], "created_at": r[3], "updated_at": r[4]}
        for r in rows
    ]


# === ROUTES ===

@router.get("/")
async def get_jobs():
    """List all recent background jobs."""
    data = list_jobs()
    return JSONResponse(content={"object": "list", "data": data})


@router.post("/")
async def create_job(body: Dict[str, Any] = Body(...)):
    """
    Create a new asynchronous job.
    Can be used for fine_tuning, batch imports, or relay tasks.
    """
    job_type = body.get("type", "custom")
    params = body.get("params", {})

    job_id = create_job_record(job_type, params)

    # Try forwarding to relay if applicable
    try:
        relay = await forward_openai(
            path="/v1/jobs",
            method="POST",
            json={"id": job_id, "type": job_type, "status": "queued", "params": params},
        )
    except Exception as e:
        relay = {"error": f"Relay job creation failed: {e}"}

    update_job_status(job_id, "running", result={"relay": relay})
    return JSONResponse(content={"object": "job", "id": job_id, "status": "running", "relay": relay})


@router.get("/{job_id}")
async def get_job_status(job_id: str):
    """Retrieve job details and progress."""
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return JSONResponse(content={"object": "job", **job})


@router.post("/{job_id}/cancel")
async def cancel_job(job_id: str):
    """Cancel a running job both locally and on the relay."""
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    try:
        relay = await forward_openai(path=f"/v1/jobs/{job_id}/cancel", method="POST")
        update_job_status(job_id, "cancelled", result={"relay": relay})
    except Exception as e:
        update_job_status(job_id, "cancelled", result={"error": str(e)})

    return JSONResponse(content={"status": "cancelled", "id": job_id})


@router.get("/ping")
async def job_ping():
    """Basic health check for the jobs subsystem."""
    return JSONResponse(content={
        "object": "jobs_ping",
        "status": "ok",
        "jobs_tracked": len(list_jobs(100)),
        "timestamp": int(time.time()),
        "version": "v2.2",
    })
