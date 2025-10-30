"""
ChatGPT Team Relay — OpenAI Forwarder
-------------------------------------
Handles forwarding of all HTTP requests from the relay
to the OpenAI API with proper authentication, timeout,
and JSON/data/file support.

Replaces earlier versions that used `json_data` (deprecated).
"""

import os
import httpx
from fastapi import HTTPException

OPENAI_BASE_URL = "https://api.openai.com/"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    print("[WARN] No OPENAI_API_KEY found in environment.")

async def forward_openai_request(
    path: str,
    method: str = "GET",
    params: dict | None = None,
    data: dict | None = None,
    json: dict | None = None,
    files: dict | None = None,
    stream: bool = False,
):
    """
    Forwards a request to the OpenAI API.

    Args:
        path (str): API path (e.g. "v1/models")
        method (str): HTTP verb
        params (dict): Query parameters
        data (dict): Form data
        json (dict): JSON payload
        files (dict): Multipart files
        stream (bool): If True, returns an async stream
    """
    url = f"{OPENAI_BASE_URL.rstrip('/')}/{path.lstrip('/')}"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=90.0) as client:
        try:
            if stream:
                # Streamed response (SSE style)
                return client.stream(
                    method, url, params=params, data=data, json=json, files=files, headers=headers
                )
            else:
                response = await client.request(
                    method, url, params=params, data=data, json=json, files=files, headers=headers
                )
        except httpx.RequestError as e:
            raise HTTPException(status_code=500, detail=f"OpenAI request failed: {str(e)}")

    if response.status_code >= 400:
        print(f"[Relay] OpenAI API Error ({response.status_code}): {response.text}")
    return response
