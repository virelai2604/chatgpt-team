from fastapi import APIRouter, Request, Response
import httpx

router = APIRouter()

@router.api_route("/v1/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
async def proxy_openai_v1(request: Request, path: str):
    target_url = f"https://api.openai.com/v1/{path}"
    headers = {k: v for k, v in request.headers.items() if k.lower() not in ["host", "content-length", "transfer-encoding"]}
    body = await request.body()
    async with httpx.AsyncClient(timeout=None) as client:
        response = await client.request(
            request.method,
            target_url,
            headers=headers,
            content=body,
            params=dict(request.query_params),
            follow_redirects=True
        )
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers={k: v for k, v in response.headers.items() if k.lower() not in ["content-encoding", "transfer-encoding", "content-length", "connection"]}
        )
