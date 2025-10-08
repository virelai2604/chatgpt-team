import os
from fastapi import Request
from fastapi.responses import StreamingResponse, Response, JSONResponse
import httpx
from dotenv import load_dotenv

# Load .env file from project root
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_ORG_ID = os.getenv("OPENAI_ORG_ID")

async def forward_openai(request: Request, endpoint: str):
    body = await request.body()

    # Relay all headers except 'host', 'authorization', 'openai-organization' (case-insensitive)
    headers = {
        k.decode(): v.decode()
        for k, v in request.headers.raw
        if k.decode().lower() not in ["host", "authorization", "openai-organization"]
    }
    headers["Authorization"] = f"Bearer {OPENAI_API_KEY}"
    if OPENAI_ORG_ID:
        headers["OpenAI-Organization"] = OPENAI_ORG_ID

    url = f"https://api.openai.com{endpoint}"

    # Debug log for troubleshooting
    print(f"Forwarding {request.method} {url}")
    print("Proxy headers:", headers)
    print("Body length:", len(body))

    wants_stream = (
        "text/event-stream" in headers.get("accept", "")
        or "text/event-stream" in headers.get("content-type", "")
        or headers.get("accept", "") == "application/octet-stream"
    )

    try:
        async with httpx.AsyncClient(timeout=None) as client:
            if wants_stream:
                async with client.stream(
                    method=request.method,
                    url=url,
                    headers=headers,
                    content=body
                ) as resp:
                    if resp.status_code >= 400 and not resp.headers.get("content-type", "").startswith("text/event-stream"):
                        content = await resp.aread()
                        print("Upstream error, status:", resp.status_code)
                        return Response(
                            content=content,
                            status_code=resp.status_code,
                            headers=dict(resp.headers),
                            media_type=resp.headers.get("content-type")
                        )
                    async def streamer():
                        try:
                            async for chunk in resp.aiter_bytes():
                                yield chunk
                        except httpx.StreamClosed:
                            print("Stream closed early")
                            return
                        except Exception as ex:
                            print("Error streaming:", ex)
                            return
                    return StreamingResponse(
                        streamer(),
                        status_code=resp.status_code,
                        headers=dict(resp.headers),
                        media_type=resp.headers.get("content-type")
                    )
            else:
                resp = await client.request(
                    method=request.method,
                    url=url,
                    headers=headers,
                    content=body
                )
                print("Upstream status:", resp.status_code)
                return Response(
                    content=resp.content,
                    status_code=resp.status_code,
                    headers=dict(resp.headers),
                    media_type=resp.headers.get("content-type")
                )
    except Exception as e:
        print("Proxy error:", str(e))
        return JSONResponse(
            status_code=502,
            content={"error": {"type": "proxy_error", "message": str(e)}}
        )
