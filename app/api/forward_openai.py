"""
ChatGPT Team Relay — OpenAI API Forwarder (v2.3.4-fp)
Ground-truth-aligned proxy for /v1/* routes, including /v1/responses.
Implements SSE streaming, tool schema normalization, and local routing.
"""

import os, json, asyncio, pprint, httpx
from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse
from dotenv import load_dotenv

load_dotenv()
router = APIRouter()

OPENAI_API_KEY  = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com")

# global HTTP client
client = httpx.AsyncClient(
    timeout=httpx.Timeout(120.0, connect=10.0),
    follow_redirects=True,
    http2=True,
)

# -------------------------------------------------------------------
# 🔄 Streaming helper — identical to OpenAI SSE format
# -------------------------------------------------------------------
async def _stream_response(upstream: httpx.Response) -> StreamingResponse:
    """Relays OpenAI's Server-Sent Events exactly as specified."""
    headers = dict(upstream.headers)
    headers.pop("content-length", None)
    headers.pop("transfer-encoding", None)

    async def gen():
        try:
            async for line in upstream.aiter_lines():
                if line.strip():
                    yield f"data: {line}\n\n"
            yield "data: [DONE]\n\n"
        except httpx.StreamClosed:
            return
        except Exception as e:
            print(f"[Relay Stream Error] {type(e).__name__}: {e}")

    return StreamingResponse(gen(), media_type="text/event-stream", headers=headers)

# -------------------------------------------------------------------
# 🧠 Local /v1/responses handler (non-stream & stream)
# -------------------------------------------------------------------
@router.post("/v1/responses")
async def handle_local_responses(request: Request):
    try:
        payload = await request.json()
    except Exception:
        payload = {}

    # ensure OpenAI-spec compliance
    payload.setdefault("model", "gpt-4o")
    payload.setdefault("parallel_tool_calls", True)
    payload.setdefault("store", True)

    # normalize token naming
    if "max_tokens" in payload and "max_output_tokens" not in payload:
        payload["max_output_tokens"] = payload.pop("max_tokens")

    # normalize tool schema
    if "tools" in payload:
        fixed = []
        for tool in payload["tools"]:
            fn = tool.get("function", {})
            if "name" not in tool and "name" in fn:
                tool["name"] = fn["name"]
            fixed.append({
                "type": tool.get("type", "function"),
                "name": tool["name"],
                "function": fn
            })
        payload["tools"] = fixed

    stream = payload.get("stream", False)
    url = f"{OPENAI_BASE_URL}/v1/responses"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    print(f">>> Forwarding {'streaming' if stream else 'buffered'} request to {url}")
    pprint.pprint(payload)

    try:
        if stream:
            async with client.stream("POST", url, headers=headers, json=payload) as upstream:
                return await _stream_response(upstream)
        else:
            resp = await client.post(url, headers=headers, json=payload)
            data = await resp.aread()
            try:
                return JSONResponse(status_code=resp.status_code, content=json.loads(data))
            except Exception:
                return Response(content=data, status_code=resp.status_code)
    except httpx.RequestError as e:
        return JSONResponse(status_code=502, content={"error": "upstream_unreachable", "detail": str(e)})
    except asyncio.TimeoutError:
        return JSONResponse(status_code=504, content={"error": "timeout", "detail": "Upstream timed out."})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": "relay_internal_error", "detail": str(e)})

# -------------------------------------------------------------------
# 🌐 Generic OpenAI forwarder — for all /v1/* routes
# -------------------------------------------------------------------
@router.api_route("/v1/{path:path}", methods=["GET", "POST", "DELETE", "PATCH"])
async def forward_openai(request: Request, path: str):
    """Catch-all proxy for OpenAI API routes (ground-truth aligned)."""
    method = request.method
    url = f"{OPENAI_BASE_URL.rstrip('/')}/{path.lstrip('/')}"
    headers = {k: v for k, v in request.headers.items() if k.lower() not in {"host","content-length","transfer-encoding"}}
    headers["Authorization"] = f"Bearer {OPENAI_API_KEY}"

    try:
        json_data = await request.json()
    except Exception:
        body = await request.body()
        try:
            json_data = json.loads(body.decode()) if body else {}
        except Exception:
            json_data = {}

    # token normalization
    if "max_tokens" in json_data and "max_output_tokens" not in json_data:
        json_data["max_output_tokens"] = json_data.pop("max_tokens")

    try:
        if method == "POST":
            if json_data.get("stream"):
                async with client.stream("POST", url, headers=headers, json=json_data) as r:
                    return await _stream_response(r)
            r = await client.post(url, headers=headers, json=json_data)
        elif method == "GET":
            r = await client.get(url, headers=headers)
        elif method == "DELETE":
            r = await client.delete(url, headers=headers)
        elif method == "PATCH":
            r = await client.patch(url, headers=headers, json=json_data)
        else:
            return JSONResponse(status_code=405, content={"error": "method_not_allowed"})

        return Response(content=await r.aread(),
                        status_code=r.status_code,
                        media_type=r.headers.get("content-type"))
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": "relay_internal_error", "detail": str(e)})

@router.on_event("shutdown")
async def close_client():
    await client.aclose()
