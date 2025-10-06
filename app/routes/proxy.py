from fastapi import APIRouter, Request, Response
import httpx
import os

router = APIRouter()

OPENAI_URL_BASE = "https://api.openai.com/v1"

async def forward_openai(request: Request, endpoint: str):
    """
    Forward any request to OpenAI API v1 with your relay’s credentials.
    Ensures only your API key is used. All methods supported.
    """
    method = request.method
    url = f"{OPENAI_URL_BASE}/{endpoint.lstrip('/')}"
    # Copy headers except these, always inject our own Authorization header
    headers = {
        k: v for k, v in request.headers.items()
        if k.lower() not in {"host", "content-length", "transfer-encoding"}
    }
    headers["Authorization"] = f"Bearer {os.environ.get('OPENAI_API_KEY', '')}"
    org = os.environ.get("OPENAI_ORG_ID")
    if org:
        headers["OpenAI-Organization"] = org
    params = dict(request.query_params)
    content = await request.body() if method in ("POST", "PUT", "PATCH") else None

    async with httpx.AsyncClient(timeout=None) as client:
        resp = await client.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            content=content,
            follow_redirects=True,
        )
        return Response(
            content=resp.content,
            status_code=resp.status_code,
            headers={k: v for k, v in resp.headers.items() if k.lower() not in {
                "content-encoding", "transfer-encoding", "content-length", "connection"
            }}
        )

@router.api_route("/v1/{endpoint:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
async def openai_passthrough(request: Request, endpoint: str):
    """
    Catch-all proxy for /v1/* endpoints. Always LAST in main.py includes!
    """
    return await forward_openai(request, endpoint)
