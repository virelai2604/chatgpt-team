import json
import os
from typing import AsyncGenerator, Dict, Any

import httpx
from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse

# All local routes in this file live under /v1
router = APIRouter(prefix="/v1", tags=["responses"])

# IMPORTANT:
# - OPENAI_API_BASE is the ROOT, WITHOUT /v1
#   e.g. https://api.openai.com
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_ORG_ID = os.getenv("OPENAI_ORG_ID", "")
RELAY_TIMEOUT = float(os.getenv("RELAY_TIMEOUT", "120"))
USER_AGENT = os.getenv("RELAY_USER_AGENT", "chatgpt-team-relay/1.0")


def _responses_url() -> str:
    """
    Build the upstream URL for the Responses API.

    Ground truth:
        POST /v1/responses
        GET  /v1/responses/{id}
    """
    base = OPENAI_API_BASE.rstrip("/")
    return f"{base}/v1/responses"


def _build_headers(request: Request) -> Dict[str, str]:
    """
    Build headers for upstream OpenAI calls.

    - Always includes Authorization and User-Agent.
    - Optionally sets OpenAI-Organization.
    - Forwards a few relevant headers from the client:
      OpenAI-Project, OpenAI-Beta, X-Request-Id, Accept (for SSE).
    """
    if not OPENAI_API_KEY:
        # This should normally be caught at startup / config level,
        # but keep a defensive check here as well.
        raise HTTPException(
            status_code=500,
            detail="OPENAI_API_KEY is not configured on the relay.",
        )

    headers: Dict[str, str] = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "User-Agent": USER_AGENT,
        "Content-Type": "application/json",
    }

    if OPENAI_ORG_ID:
        headers["OpenAI-Organization"] = OPENAI_ORG_ID

    # Forward selected headers from the client
    # - OpenAI-Project, OpenAI-Beta: project routing / beta flags
    # - X-Request-Id: observability / tracing
    # - Accept: allows clients to request SSE explicitly
    for key in ("OpenAI-Project", "OpenAI-Beta", "X-Request-Id", "Accept"):
        if key in request.headers:
            headers[key] = request.headers[key]

    return headers


async def _stream_upstream_sse(
    client: httpx.AsyncClient,
    url: str,
    headers: Dict[str, str],
    body: Dict[str, Any],
) -> StreamingResponse:
    """
    Open a streaming POST to /v1/responses and forward all raw chunks
    to the client as-is (SSE or chunked JSON).
    """

    async def event_source() -> AsyncGenerator[bytes, None]:
        async with client.stream("POST", url, headers=headers, json=body) as res:
            # If upstream returns an error HTTP code, surface it quickly.
            if res.status_code >= 400:
                text = await res.aread()
                # We cannot raise HTTPException inside the generator cleanly,
                # so we yield the error body and let the client handle it.
                # For most cases, the caller should prefer non-streaming mode
                # when relying on status codes strictly.
                yield text
                return

            async for chunk in res.aiter_raw():
                if chunk:
                    yield chunk

    # We cannot know the exact content-type until the first response,
    # but for SSE we default to text/event-stream. If upstream sets a more
    # specific header, the client will still receive compliant frames.
    return StreamingResponse(
        event_source(),
        status_code=200,
        media_type="text/event-stream",
    )


@router.post("/responses")
async def create_response(request: Request):
    """
    POST /v1/responses

    This proxies the unified Responses API to OpenAI, supporting both
    streaming and non-streaming usage.

    Streaming detection:
      - Primary: body["stream"] == true
      - Secondary: Accept: text/event-stream
    """
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    # Primary signal: explicit `stream: true` in the JSON payload
    has_stream_flag = bool(body.get("stream", False))

    # Optional signal: client advertises it wants SSE
    accept_header = request.headers.get("accept", "").lower()
    wants_sse = "text/event-stream" in accept_header

    # We stream if either condition is true
    should_stream = has_stream_flag or wants_sse

    url = _responses_url()
    headers = _build_headers(request)

    async with httpx.AsyncClient(timeout=RELAY_TIMEOUT) as client:
        if should_stream:
            # SSE / streaming mode: raw passthrough of upstream chunks
            return await _stream_upstream_sse(client, url, headers, body)

        # Non-streaming mode
        upstream = await client.post(url, headers=headers, json=body)

    # Surface upstream errors directly
    if upstream.status_code >= 400:
        # Try to parse OpenAI-style error JSON; fall back to text if needed.
        try:
            detail = upstream.json()
        except Exception:
            detail = upstream.text
        raise HTTPException(status_code=upstream.status_code, detail=detail)

    # Successful non-streaming response
    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        media_type=upstream.headers.get("content-type", "application/json"),
    )


@router.get("/responses/{response_id}")
async def get_response(response_id: str, request: Request):
    """
    GET /v1/responses/{id}

    Proxy to the OpenAI Responses API to retrieve a previously-created
    response object by ID.
    """
    url = f"{_responses_url()}/{response_id}"
    headers = _build_headers(request)

    async with httpx.AsyncClient(timeout=RELAY_TIMEOUT) as client:
        upstream = await client.get(url, headers=headers)

    if upstream.status_code >= 400:
        try:
            detail = upstream.json()
        except Exception:
            detail = upstream.text
        raise HTTPException(
            status_code=upstream.status_code,
            detail=detail,
        )

    # Return the JSON exactly as OpenAI provides it
    return JSONResponse(
        status_code=upstream.status_code,
        content=upstream.json(),
    )
