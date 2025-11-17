import os

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse

router = APIRouter(prefix="/v1/videos", tags=["videos"])

OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_ORG_ID = os.getenv("OPENAI_ORG_ID", "")
RELAY_TIMEOUT = float(os.getenv("RELAY_TIMEOUT", "300"))  # videos can take longer

# Optional beta flag for future video features. At the time of writing, the
# Sora Video API doesn't require an explicit OpenAI-Beta header, but we
# support configuring one to stay future-proof.
OPENAI_VIDEOS_BETA = os.getenv("OPENAI_VIDEOS_BETA", "")


def _base_url(path: str) -> str:
    return f"{OPENAI_API_BASE.rstrip('/')}{path}"


def video_headers(request: Request | None = None, is_json: bool = True) -> dict:
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not configured")

    headers: dict[str, str] = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
    }

    if is_json:
        headers["Content-Type"] = "application/json"

    if OPENAI_ORG_ID:
        headers["OpenAI-Organization"] = OPENAI_ORG_ID

    beta = OPENAI_VIDEOS_BETA.strip()
    if not beta and request is not None:
        beta = request.headers.get("OpenAI-Beta", "").strip()

    if beta:
        headers["OpenAI-Beta"] = beta

    return headers


async def _proxy_json(
    method: str,
    path: str,
    request: Request | None = None,
    body: dict | None = None,
) -> JSONResponse:
    async with httpx.AsyncClient(timeout=RELAY_TIMEOUT) as client:
        url = _base_url(path)
        kwargs = {"headers": video_headers(request, is_json=True)}
        if body is not None:
            kwargs["json"] = body

        upstream = await client.request(method, url, **kwargs)

    if upstream.is_error:
        raise HTTPException(
            status_code=upstream.status_code,
            detail=upstream.text,
        )

    return JSONResponse(
        status_code=upstream.status_code,
        content=upstream.json(),
    )


@router.post("")
async def create_video(request: Request) -> JSONResponse:
    """
    POST /v1/videos

    Mirrors client.videos.create(...) in the official SDKs:
    - Create a new Sora video job from a prompt and optional inputs. 
    """
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    return await _proxy_json("POST", "/v1/videos", request=request, body=body)


@router.get("")
async def list_videos(request: Request) -> JSONResponse:
    """
    GET /v1/videos

    List existing video jobs for the API key/project.
    """
    return await _proxy_json("GET", "/v1/videos", request=request)


@router.get("/{video_id}")
async def retrieve_video(video_id: str, request: Request) -> JSONResponse:
    """
    GET /v1/videos/{video_id}

    Retrieve the status and metadata for a single video job.
    """
    path = f"/v1/videos/{video_id}"
    return await _proxy_json("GET", path, request=request)


@router.delete("/{video_id}")
async def delete_video(video_id: str, request: Request) -> JSONResponse:
    """
    DELETE /v1/videos/{video_id}

    Delete a video job and its stored content.
    """
    path = f"/v1/videos/{video_id}"
    return await _proxy_json("DELETE", path, request=request)


@router.get("/{video_id}/content")
async def download_video_content(video_id: str, request: Request) -> StreamingResponse:
    """
    GET /v1/videos/{video_id}/content

    Stream the raw MP4 (or other configured variant) back to the caller.
    The SDKs expose this as client.videos.download_content(...). 
    """
    async with httpx.AsyncClient(timeout=RELAY_TIMEOUT) as client:
        url = _base_url(f"/v1/videos/{video_id}/content")
        upstream = await client.get(
            url,
            headers=video_headers(request, is_json=False),
            timeout=RELAY_TIMEOUT,
        )

    if upstream.is_error:
        raise HTTPException(
            status_code=upstream.status_code,
            detail=upstream.text,
        )

    # Stream binary content through
    async def content_generator():
        yield upstream.content

    media_type = upstream.headers.get("Content-Type", "application/octet-stream")
    return StreamingResponse(content_generator(), media_type=media_type)
