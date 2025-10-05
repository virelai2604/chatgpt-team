from fastapi import APIRouter, Request, Response
from fastapi.responses import StreamingResponse
import httpx
import os

router = APIRouter()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_ORG_ID = os.getenv("OPENAI_ORG_ID", "")
OPENAI_BASE_URL = "https://api.openai.com"

def build_headers():
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }
    if OPENAI_ORG_ID:
        headers["OpenAI-Organization"] = OPENAI_ORG_ID
    return headers

@router.api_route("/v1/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
async def proxy_v1(request: Request, path: str):
    dest_url = f"{OPENAI_BASE_URL}/v1/{path}"
    headers = build_headers()
    method = request.method
    params = request.query_params

    async with httpx.AsyncClient(timeout=None) as client:
        if method in ("POST", "PUT", "PATCH"):
            body = await request.body()
            resp = await client.request(method, dest_url, headers=headers, params=params, content=body)
        else:
            resp = await client.request(method, dest_url, headers=headers, params=params)

        if resp.headers.get("content-type", "").startswith("text/event-stream"):
            return StreamingResponse(resp.aiter_bytes(), media_type="text/event-stream")
        return Response(content=resp.content, status_code=resp.status_code, headers=dict(resp.headers))

@router.api_route("/openai/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
async def proxy_openai(request: Request, path: str):
    dest_url = f"{OPENAI_BASE_URL}/openai/{path}"
    headers = build_headers()
    method = request.method
    params = request.query_params

    async with httpx.AsyncClient(timeout=None) as client:
        if method in ("POST", "PUT", "PATCH"):
            body = await request.body()
            resp = await client.request(method, dest_url, headers=headers, params=params, content=body)
        else:
            resp = await client.request(method, dest_url, headers=headers, params=params)

        if resp.headers.get("content-type", "").startswith("text/event-stream"):
            return StreamingResponse(resp.aiter_bytes(), media_type="text/event-stream")
        return Response(content=resp.content, status_code=resp.status_code, headers=dict(resp.headers))
