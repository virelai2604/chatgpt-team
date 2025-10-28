from fastapi import APIRouter, Request, Response
from fastapi.responses import StreamingResponse, JSONResponse
import httpx, os, json, asyncio, pprint
from dotenv import load_dotenv

load_dotenv()
router = APIRouter()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com")
MAX_RELAY_RESPONSE_BYTES = 4_000_000

client = httpx.AsyncClient(
    timeout=httpx.Timeout(120.0, connect=10.0),
    follow_redirects=True,
    http2=True,
)

async def _stream_response(resp: httpx.Response):
    headers = dict(resp.headers)
    headers.pop("content-length", None)
    headers.pop("transfer-encoding", None)
    async def gen():
        async for chunk in resp.aiter_bytes():
            yield chunk
    return StreamingResponse(gen(), status_code=resp.status_code, headers=headers)

async def _buffer_response(resp: httpx.Response):
    content = await resp.aread()
    if len(content) > MAX_RELAY_RESPONSE_BYTES:
        return JSONResponse(status_code=502, content={"error": "ResponseTooLargeError"})
    try:
        data = json.loads(content)
        return JSONResponse(status_code=resp.status_code, content=data)
    except Exception:
        return Response(content=content, status_code=resp.status_code)

@router.api_route("/v1/{path:path}", methods=["GET", "POST", "DELETE", "PATCH"])
async def forward_openai(request: Request, path: str):
    method = request.method
    url = f"{OPENAI_BASE_URL.rstrip('/')}/{path.lstrip('/')}"

    headers = {**request.headers, "Authorization": f"Bearer {OPENAI_API_KEY}"}
    for key in ["host", "content-length", "transfer-encoding"]:
        headers.pop(key, None)

    try:
        json_data = await request.json()
    except Exception:
        body_bytes = await request.body()
        json_data = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}

    print(f"\n>>> Forwarding {method} {url}")
    pprint.pprint(json_data)

    # --- Ground truth corrections (from OpenAI spec) ---
    if "tools" in json_data:
        for tool in json_data["tools"]:
            if "name" not in tool and "function" in tool and "name" in tool["function"]:
                too
