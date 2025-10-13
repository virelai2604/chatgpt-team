from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from app.api.forward import forward_openai

router = APIRouter(prefix="/threads")

@router.post("")
async def create_thread(request: Request):
    """Create a new thread."""
    return await forward_openai(request, "/v1/threads")

@router.get("/{thread_id}")
async def get_thread(request: Request, thread_id: str):
    """Get thread info."""
    return await forward_openai(request, f"/v1/threads/{thread_id}")

@router.post("/{thread_id}/messages")
async def add_thread_message(request: Request, thread_id: str):
    """Add a message to a thread."""
    return await forward_openai(request, f"/v1/threads/{thread_id}/messages")

@router.get("/{thread_id}/messages")
async def list_thread_messages(request: Request, thread_id: str):
    """List all messages in a thread."""
    return await forward_openai(request, f"/v1/threads/{thread_id}/messages")

@router.post("/{thread_id}/runs")
async def create_run(request: Request, thread_id: str):
    """Create a new run for a thread."""
    return await forward_openai(request, f"/v1/threads/{thread_id}/runs")

@router.get("/{thread_id}/runs")
async def list_runs(request: Request, thread_id: str):
    """List all runs for a thread."""
    return await forward_openai(request, f"/v1/threads/{thread_id}/runs")

@router.get("/{thread_id}/runs/{run_id}/steps")
async def list_run_steps(request: Request, thread_id: str, run_id: str):
    """List all steps in a run."""
    return await forward_openai(request, f"/v1/threads/{thread_id}/runs/{run_id}/steps")

# Deprecated endpoint for v1: respond with 410 Gone (BIFL-grade explicit)
@router.post("/attach_file")
async def deprecated_attach_file(request: Request):
    return JSONResponse(
        {"error": "Deprecated in v2. Use thread/message file upload."}, status_code=410
    )
