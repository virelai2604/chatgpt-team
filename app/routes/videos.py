import os
import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse, JSONResponse
import mimetypes
import logging

router = APIRouter()

VIDEO_MODE = os.environ.get("VIDEO_MODE", "remote")
VIDEO_DIR = os.environ.get("VIDEO_DIR", "./videos")
VIDEO_CDN = os.environ.get("VIDEO_CDN", "")
OPENAI_BASE = os.environ.get("OPENAI_BASE", "https://api.openai.com/v1")
OPENAI_KEY = os.environ.get("OPENAI_API_KEY", "")

def openai_headers():
    return {"Authorization": f"Bearer {OPENAI_KEY}"}

async def file_streamer(path, chunk_size=65536):
    with open(path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            yield chunk

async def remote_streamer(url, mime):
    async with httpx.AsyncClient() as client:
        async with client.stream("GET", url) as resp:
            if resp.status_code == 200:
                return StreamingResponse(resp.aiter_bytes(), media_type=mime)
            elif resp.status_code == 404:
                return None
            else:
                logging.error(f"Remote fetch failed: {url} ({resp.status_code})")
                raise HTTPException(status_code=resp.status_code, detail=f"Remote video fetch failed: {url}")

async def openai_streamer(video_id):
    # Official OpenAI content endpoint for video download
    url = f"{OPENAI_BASE}/videos/{video_id}/content"
    headers = openai_headers()
    async with httpx.AsyncClient() as client:
        async with client.stream("GET", url, headers=headers) as resp:
            if resp.status_code == 200:
                # The correct content-type will be provided by OpenAI (usually video/mp4)
                return StreamingResponse(resp.aiter_bytes(), media_type=resp.headers.get("content-type", "video/mp4"))
            elif resp.status_code == 404:
                return None
            else:
                raise HTTPException(status_code=resp.status_code, detail="OpenAI video fetch failed")

def find_video_file(video_id):
    for ext in (".mp4", ".mov", ".gif"):
        candidate = os.path.join(VIDEO_DIR, f"{video_id}{ext}")
        if os.path.isfile(candidate):
            return candidate, mimetypes.guess_type(candidate)[0] or "video/mp4"
    return None, None

@router.get("/videos/{video_id}/content")
async def stream_video_content(video_id: str):
    """
    Streams video content for a given video_id.
    Tries local, CDN, then falls back to OpenAI API.
    """
    # 1. Local file
    if VIDEO_MODE == "local":
        path, mime = find_video_file(video_id)
        if path:
            return StreamingResponse(file_streamer(path), media_type=mime)
    # 2. CDN/remote
    if VIDEO_CDN:
        for ext in (".mp4", ".mov", ".gif"):
            url = f"{VIDEO_CDN.rstrip('/')}/{video_id}{ext}"
            mime = mimetypes.guess_type(url)[0] or "video/mp4"
            try:
                resp = await remote_streamer(url, mime)
                if resp:
                    return resp
            except HTTPException as e:
                if e.status_code != 404:
                    raise
    # 3. OpenAI remote fallback (BIFL v2, docs-compliant)
    resp = await openai_streamer(video_id)
    if resp:
        return resp

    logging.warning(f"Video not found anywhere: {video_id}")
    raise HTTPException(status_code=404, detail="Video file not found (local, remote, or OpenAI)")

# The rest: Proxy to OpenAI as before

@router.post("/videos")
async def create_video(request: Request):
    async with httpx.AsyncClient() as client:
        payload = await request.json()
        r = await client.post(
            f"{OPENAI_BASE}/videos",
            json=payload,
            headers=openai_headers()
        )
        return JSONResponse(content=r.json(), status_code=r.status_code)

@router.get("/videos/{video_id}")
async def get_video_status(video_id: str):
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{OPENAI_BASE}/videos/{video_id}",
            headers=openai_headers()
        )
        return JSONResponse(content=r.json(), status_code=r.status_code)

@router.delete("/videos/{video_id}")
async def delete_video(video_id: str):
    async with httpx.AsyncClient() as client:
        r = await client.delete(
            f"{OPENAI_BASE}/videos/{video_id}",
            headers=openai_headers()
        )
        return JSONResponse(content=r.json(), status_code=r.status_code)

@router.post("/videos/{video_id}/remix")
async def remix_video(video_id: str, request: Request):
    async with httpx.AsyncClient() as client:
        payload = await request.json()
        r = await client.post(
            f"{OPENAI_BASE}/videos/{video_id}/remix",
            json=payload,
            headers=openai_headers()
        )
        return JSONResponse(content=r.json(), status_code=r.status_code)
