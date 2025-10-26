# BIFL v2.3.3 — Unified Video Generation + Remixing
# Uses /v1/responses with tools[] instead of deprecated /v1/videos direct jobs.

import os, json, uuid, time, asyncio, sqlite3
from fastapi import APIRouter, HTTPException, Body
from fastapi.responses import JSONResponse, StreamingResponse
from app.routes.core import forward_openai

router = APIRouter(prefix="/v1/videos", tags=["Videos"])

VIDEO_DIR = os.getenv("VIDEO_DIR", "data/videos")
DB_PATH = os.path.join(VIDEO_DIR, "videos.db")
os.makedirs(VIDEO_DIR, exist_ok=True)

def record_video_job(model, prompt, seconds, purpose="video_generation", remixed_from=None):
    job_id = str(uuid.uuid4())
    with sqlite3.connect(DB_PATH) as db:
        db.execute(
            "CREATE TABLE IF NOT EXISTS videos (id TEXT, model TEXT, prompt TEXT, status TEXT, progress REAL, created_at INTEGER, seconds INTEGER, purpose TEXT, remixed_from TEXT)"
        )
        db.execute(
            "INSERT INTO videos VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (job_id, model, prompt, "queued", 0.0, int(time.time()), seconds, purpose, remixed_from),
        )
        db.commit()
    return job_id

@router.post("/")
async def create_video(body: dict = Body(...)):
    """Generate video using Sora 2 Pro via /v1/responses tools."""
    prompt = body.get("prompt")
    seconds = body.get("seconds", 10)
    if not prompt:
        raise HTTPException(status_code=400, detail="Missing 'prompt'")
    job_id = record_video_job("sora-2-pro", prompt, seconds)
    relay = await forward_openai(
        "/v1/responses",
        "POST",
        {
            "model": "gpt-5-pro",
            "input": f"Generate a video: {prompt}",
            "tools": [{"type": "video_generation", "model": "sora-2-pro", "parameters": {"seconds": seconds}}],
        },
    )
    return JSONResponse(content={"id": job_id, "relay": relay, "status": "queued"})

@router.post("/{video_id}/remix")
async def remix_video(video_id: str, body: dict = Body(...)):
    """Remix a previously generated video."""
    prompt = body.get("prompt", "")
    params = body.get("parameters", {"seconds": 10})
    job_id = record_video_job("sora-2-pro", prompt, params.get("seconds", 10), "video_remix", remixed_from=video_id)
    relay = await forward_openai(
        "/v1/responses",
        "POST",
        {
            "model": "gpt-5-pro",
            "input": f"Remix video {video_id}: {prompt}",
            "tools": [{"type": "video_generation", "model": "sora-2-pro", "parameters": params}],
        },
    )
    return JSONResponse(content={"object": "video_remix", "id": job_id, "relay": relay})

@router.get("/{video_id}/events")
async def stream_progress(video_id: str):
    """Simulated progress event stream."""
    async def progress():
        for i in range(0, 101, 20):
            yield f"data: {json.dumps({'video_id': video_id, 'progress': i})}\\n\\n"
            await asyncio.sleep(0.5)
    return StreamingResponse(progress(), media_type="text/event-stream")
