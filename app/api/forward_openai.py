"""
ChatGPT Team Relay — OpenAI API Forwarder (v2.3.4-fp)
Ground-truth aligned proxy for /v1/* routes, including /v1/responses.
Implements SSE streaming, tool schema normalization, and local routing.
"""

import os
import json
import asyncio
import pprint
import httpx
from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse
from dotenv import load_dotenv

# -------------------------------------------------------------
# 🌍 Environment & Constants
# -------------------------------------------------------------
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

# -------------------------------------------------------------
# 🧩 Streaming helper — Ground Truth SSE format (Fixed)
# -------------------------------------------------------------
async def _stream_response(upstream: httpx.Response) -> StreamingResponse:
    """
    Relay OpenAI SSE stream in real time, following ground-truth format:
    - Each event prefixed with 'data:'
    - Stream terminates with '[DONE]'
    - Gracefully handles closed streams (no ASGI tracebacks)
    """
    headers = dict(upstream.headers)
    headers.pop("content-length", None)
    headers.pop("transfer-encoding", None)

    async def gen():
        try:
            async for line in upstream.aiter_lines():
                if line.strip():
                    yield f"data: {line}\n\n"
            # Emit sentinel end marker
            yield "data: [DONE]\n\n"
        except httpx.StreamClosed:
            # Expected when the upstream stream ends cleanly
            return
        except Exception as e:
            print(f"[Relay Stream Error] {type(e).__name__}: {e}")

    return StreamingResponse(gen(), media_type="text/event-stream", headers=headers)

# -------------------------------------------------------------
# 🧠 Local handler for /v1/responses — internal routing
# -------------------------------------------------------------
@router.post("/v1/responses")
async def handle_local_responses(request: Request):
    """
    Ground-truth aligned handler for /v1/responses.
    - Normalizes tool schema
    - Streams output if requested
    - Forwards to OpenAI if not handled locally
    """
    try:
        payload = await request.json()
    except Exception:
        payload = {}

    pprint.pprint({"received_body": payload})

    # --- Ensure model and schema correctness
    payload.setdefault("model", "gpt-4o")
    payload.setdefault("parallel_tool_calls", True)
    payload.setdefault("store", True)

    # --- Normalize token naming per OpenAI spec
    if "max_tokens" in payload and "max_output_tokens" not in payload:
        payload["max_output_tokens"] = payload.pop("max_tokens")

    # --- Enforce proper tool schema (per OpenAI spec)
    if "tools" in payload:
        fixed_tools = []
        for tool in payload["tools"]:
            fn = tool.get("function", {})
            if "name" not in tool and "name" in fn:
                tool["name"] = fn["name"]
            fixed_tools.append({
                "type": tool.get("type", "function"),
                "name": tool["name"],
                "function": fn
            })
        payload["tools"] = fixed_tools

    # --- Stream or buffer setup
    stream = payload.get("stream", False)
    url = f"{OPENAI_BASE_URL}/v1/responses"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    print(f">>> Forwarding {'streaming' if stream else 'buffered'} request to {url}")
    print(json.dumps(payload, indent=2))

    try:
        if stream:
            async with client.stream("POST", url, headers=headers, json=payload) as upstream:
                return await _stream_response(upstream)
        else:
            resp = await client.post(url, headers=headers, json=payload)
            data = await resp.aread()
            try:
                content = json.loads(data)
            except Exception:
                return Response(content=data, status_code=resp.status_code)
            return JSONResponse(status_code=resp.status_code, content=content)
    except httpx.RequestError as e:
        return JSONResponse(status_code=502, content={"error": "upstream_unreachable", "detail": str(e)})
    except asyncio.TimeoutError:
        return JSONResponse(status_code=504, content={"error": "timeout", "detail": "Upstream timed out."})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": "relay_internal_error", "detail": str(e)})

# -------------------------------------------------------------
# 🌐 Generic OpenAI Forwarder (fallback for all /v1/* routes)
# -------------------------------------------------------------
@router.api_route("/v1/{path:path}", methods=["GET", "POST", "DELETE", "PATCH"])
async def forward_openai(request: Request, path: str):
    """Catch-all proxy for OpenAI API routes (ground-truth aligned)."""
    method = request.method
    url = f"{OPENAI_BASE_URL.rstrip('/')}/{path.lstrip('/')}"
    headers = dict(request.headers)
    headers["Authorization"] = f"Bearer {OPENAI_API_KEY}"
    for k in ["host", "content-length", "transfer-encoding"]:
        headers.pop(k, None)

    try:
        json_data = await request.json()
    except Exception:
        body = await request.body()
        try:
            json_data = json.loads(body.decode("utf-8")) if body else {}
        except Exception:
            json_data = {}

    print(f"\n>>> Forwarding {method} {url}")
    pprint.pprint(json_data)

    # Ground-truth corrections for legacy clients
    if "max_tokens" in json_data and "max_output_tokens" not in json_data:
        json_data["max_output_tokens"] = json_data.pop("max_tokens")

    try:
        if method == "POST":
            if json_data.get("stream", False):
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

        print(f"[Relay → OpenAI] {r.status_code} {url}")
        return Response(content=await r.aread(), status_code=r.status_code, media_type=r.headers.get("content-type"))
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": "relay_internal_error", "detail": str(e)})

# -------------------------------------------------------------
# 🧹 Cleanup
# -------------------------------------------------------------
@router.on_event("shutdown")
async def close_client():
    await client.aclose()
