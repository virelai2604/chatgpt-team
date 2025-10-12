from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from app.api.forward import forward_openai
import httpx
import os

router = APIRouter()

@router.post("/")
async def create_video(request: Request):
    # Pass-through to OpenAI /v1/videos
    return await forward_openai(request, "/v1/videos")

@router.get("/{video_id}")
async def get_video_status(video_id: str, request: Request):
    # Pass-through to OpenAI /v1/videos/{video_id}
    return await forward_openai(request, f"/v1/videos/{video_id}")

@router.post("/{video_id}/remix")
async def remix_video(video_id: str, request: Request):
    # Pass-through to OpenAI /v1/videos/{video_id}/remix
    return await forward_openai(request, f"/v1/videos/{video_id}/remix")

@router.get("/{video_id}/content")
async def stream_video_content(video_id: str):
    """
    Streams generated MP4, MOV, or GIF video, local or from remote CDN, BIFL-style.
    """
    VIDEO_MODE = os.getenv("VIDEO_STREAM_MODE", "remote")
    VIDEO_DIR = os.getenv("VIDEO_STREAM_DIR", "/videos")
    VIDEO_URL_TEMPLATE = os.getenv(
        "VIDEO_STREAM_URL", "https://cdn.yourapp.com/videos/{video_id}.{ext}"
    )

    # Try .mp4, then .mov, then .gif
    for ext, mime in [("mp4", "video/mp4"), ("mov", "video/quicktime"), ("gif", "image/gif")]:
        if VIDEO_MODE == "local":
            video_path = os.path.join(VIDEO_DIR, f"{video_id}.{ext}")
            if os.path.isfile(video_path):
                def iterfile():
                    with open(video_path, "rb") as f:
                        while chunk := f.read(8192):
                            yield chunk
                return StreamingResponse(iterfile(), media_type=mime)
        elif VIDEO_MODE == "remote":
            video_url = VIDEO_URL_TEMPLATE.format(video_id=video_id, ext=ext)
            async with httpx.AsyncClient() as client:
                resp = await client.get(video_url, stream=True)
                if resp.status_code == 200:
                    return StreamingResponse(resp.aiter_bytes(), media_type=mime)

    raise HTTPException(status_code=404, detail="Video not found")
