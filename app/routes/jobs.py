# ==========================================================
# app/routes/jobs.py — BIFL v2.3.4-fp
# ==========================================================
# Async job management proxy for OpenAI-compatible APIs.
# Supports fine-tuning, batch, and video job polling.
# ==========================================================

from fastapi import APIRouter, Request
from app.api.forward import forward_openai
from app.utils.db_logger import log_event

router = APIRouter(prefix="/v1/jobs", tags=["Jobs"])

# ----------------------------------------------------------
# 🧩  Create Job
# ----------------------------------------------------------
@router.post("")
async def create_job(request: Request):
    """
    Create a background job (fine-tune, batch, or video generation).
    Example:
        POST /v1/jobs
        { "type": "fine_tuning", "training_file": "file-123" }
    """
    response = await forward_openai(request, "/v1/jobs")
    try:
        await log_event("/v1/jobs/create", response.status_code, "job created")
    except Exception:
        pass
    return response


# ----------------------------------------------------------
# 🧾  List Jobs
# ----------------------------------------------------------
@router.get("")
async def list_jobs(request: Request):
    """List all running or completed background jobs."""
    response = await forward_openai(request, "/v1/jobs")
    try:
        await log_event("/v1/jobs/list", response.status_code, "jobs listed")
    except Exception:
        pass
    return response


# ----------------------------------------------------------
# 🔍  Retrieve Job Details
# ----------------------------------------------------------
@router.get("/{job_id}")
async def get_job(request: Request, job_id: str):
    """Get job details or status by job ID."""
    endpoint = f"/v1/jobs/{job_id}"
    response = await forward_openai(request, endpoint)
    try:
        await log_event("/v1/jobs/get", response.status_code, f"job {job_id}")
    except Exception:
        pass
    return response


# ----------------------------------------------------------
# 🧹  Cancel Job
# ----------------------------------------------------------
@router.delete("/{job_id}")
async def cancel_job(request: Request, job_id: str):
    """Cancel or delete a background job upstream."""
    endpoint = f"/v1/jobs/{job_id}"
    response = await forward_openai(request, endpoint)
    try:
        await log_event("/v1/jobs/cancel", response.status_code, f"cancel {job_id}")
    except Exception:
        pass
    return response
