# ================================================================
# forward_openai.py — OpenAI Upstream Forwarder
# ================================================================
# Forwards compatible /v1/* requests to the official OpenAI API.
# Used only when DISABLE_PASSTHROUGH=false.
#
# The design is stateless, async, and honors the SDK 2.6.1 streaming
# conventions (with optional text/event-stream passthrough).
# ================================================================

import os
import httpx
from fastapi import Request
from fastapi.responses import JSONResponse, StreamingResponse

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com")

async def forward_request(req: Request, path: str):
    """
    Forwards request to OpenAI’s live API.
    """
    method = req.method
    url = f"{OPENAI_BASE_URL}/{path}"
    headers = dict(req.headers)
    headers["Authorization"] = f"Bearer {OPENAI_API_KEY}"
    headers["Content-Type"] = "application/json"

    # Forward JSON body (if applicable)
    body = None
    if method in ("POST", "PUT", "PATCH"):
        try:
            body = await req.json()
        except Exception:
            return JSONResponse({"error": "Invalid JSON"}, status_code=400)

    async with httpx.AsyncClient(timeout=60.0) as client:
        if method == "GET":
            r = await client.get(url, headers=headers)
        elif method == "POST":
            if body and body.get("stream"):
                async with client.stream("POST", url, headers=headers, json=body) as resp:
                    return StreamingResponse(resp.aiter_text(), media_type="text/event-stream")
            r = await client.post(url, headers=headers, json=body)
        elif method == "DELETE":
            r = await client.delete(url, headers=headers)
        elif method == "PATCH":
            r = await client.patch(url, headers=headers, json=body)
        elif method == "PUT":
            r = await client.put(url, headers=headers, json=body)
        else:
            return JSONResponse({"error": "Unsupported method"}, status_code=405)

    # Proxy the response
    try:
        return JSONResponse(r.json(), status_code=r.status_code)
    except Exception:
        return JSONResponse({"error": "Upstream response not JSON"}, status_code=r.status_code)
