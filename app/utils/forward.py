import os
import httpx
from fastapi import Request, HTTPException
from starlette.responses import StreamingResponse, JSONResponse

async def forward_openai(request: Request, path: str):
    api_key = os.getenv("OPENAI_API_KEY")
    org_id = os.getenv("OPENAI_ORG_ID")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    if org_id:
        headers["OpenAI-Organization"] = org_id

    body = await request.json()
    stream = body.get("stream", False)

    if not stream:
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"https://api.openai.com/v1/{path}", json=body, headers=headers)
            resp.raise_for_status()
            return JSONResponse(content=resp.json())

    async def event_stream():
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream(
                "POST",
                f"https://api.openai.com/v1/{path}",
                headers=headers,
                json=body
            ) as resp:
                async for line in resp.aiter_lines():
                    if line.startswith("data: "):
                        yield f"{line}\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
