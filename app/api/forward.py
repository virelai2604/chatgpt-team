from fastapi import Request
from fastapi.responses import Response, JSONResponse
import httpx

async def forward_openai(request: Request, endpoint: str):
    body = await request.body()
    # Remove host header!
    headers = {k.decode(): v.decode() for k, v in request.headers.raw if k.decode() != "host"}
    url = f"https://api.openai.com{endpoint}"
    print("Forwarding to:", url)
    print("Headers:", headers)
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.request(
                method=request.method,
                url=url,
                headers=headers,
                content=body,
                timeout=60.0
            )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": {"type": "proxy_error", "message": str(e)}}
        )
    return Response(
        content=resp.content,
        status_code=resp.status_code,
        headers=dict(resp.headers),
        media_type=resp.headers.get("content-type")
    )
