import os
from fastapi import Request
from fastapi.responses import StreamingResponse, Response, JSONResponse
import httpx
from dotenv import load_dotenv
from app.utils.db_logger import save_raw_request

# Load env variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_ORG_ID = os.getenv("OPENAI_ORG_ID")

def is_beta_assistants_endpoint(endpoint: str) -> bool:
    """
    Returns True if endpoint needs v2 assistants header
    """
    return (
        endpoint.startswith("/v1/assistants") or
        endpoint.startswith("/v1/threads") or
        endpoint.startswith("/v1/vector_stores") or
        endpoint.startswith("/v1/tools")
    )

async def forward_openai(request: Request, endpoint: str):
    """
    Core relay handler: Forwards request to OpenAI, handles streaming, v2 headers, and logs request.
    """
    body = await request.body()
    headers_json = str(dict(request.headers))
    save_raw_request(endpoint=endpoint, raw_body=body, headers_json=headers_json)

    headers = {
        k.decode(): v.decode()
        for k, v in request.headers.raw
        if k.decode().lower() not in ["host", "authorization", "openai-organization"]
    }
    headers["Authorization"] = f"Bearer {OPENAI_API_KEY}"
    if OPENAI_ORG_ID:
        headers["OpenAI-Organization"] = OPENAI_ORG_ID

    # BIFL v2: Add v2 beta header for eligible endpoints
    if is_beta_assistants_endpoint(endpoint):
        headers["OpenAI-Beta"] = "assistants=v2"

    url = f"https://api.openai.com{endpoint}"

    wants_stream = (
        "text/event-stream" in headers.get("accept", "")
        or "text/event-stream" in headers.get("content-type", "")
        or headers.get("accept", "") == "application/octet-stream"
        or headers.get("accept", "") == "application/x-ndjson"
        or (("stream" in request.query_params and request.query_params["stream"] == "true"))
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
                    # Error? Relay as non-stream for readable error
                    if resp.status_code >= 400 and not resp.headers.get("content-type", "").startswith("text/event-stream"):
                        content = await resp.aread()
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
                return Response(
                    content=resp.content,
                    status_code=resp.status_code,
                    headers=dict(resp.headers),
                    media_type=resp.headers.get("content-type")
                )
    except Exception as e:
        return JSONResponse(
            status_code=502,
            content={"error": {"type": "proxy_error", "message": str(e)}}
        )
