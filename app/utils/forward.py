from fastapi import Request, Response
import httpx
import os

OPENAI_URL_BASE = "https://api.openai.com/v1"

async def forward_openai(request: Request, endpoint: str):
    method = request.method
    url = f"{OPENAI_URL_BASE}/{endpoint.lstrip('/')}"
    # Copy all headers except forbidden ones
    headers = {
        k: v
        for k, v in request.headers.items()
        if k.lower() not in {"host", "content-length", "transfer-encoding"}
    }
    # Always inject our relay's API key
    headers["Authorization"] = f"Bearer {os.environ.get('OPENAI_API_KEY', '')}"
    org = os.environ.get("OPENAI_ORG_ID")  # Use _ID for env consistency!
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
            headers={
                k: v for k, v in resp.headers.items()
                if k.lower() not in {
                    "content-encoding", "transfer-encoding", "content-length", "connection"
                }
            }
        )
