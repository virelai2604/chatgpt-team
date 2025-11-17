import json
import os
from typing import AsyncGenerator

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse

router = APIRouter(prefix="/v1", tags=["responses"])

OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_ORG_ID = os.getenv("OPENAI_ORG_ID", "")
RELAY_TIMEOUT = float(os.getenv("RELAY_TIMEOUT", "120"))
USER_AGENT = os.getenv("RELAY_USER_AGENT", "chatgpt-team-relay/1.0")

# Optional – allow forcing a specific beta flag for responses, but by default
# there is no beta header required for this family.
OPENAI_RESPONSES_BETA = os.getenv("OPENAI_RESPONSES_BETA", "")


def _base_url(path: str) -> str:
    return f"{OPENAI_API_BASE.rstrip('/')}{path}"


def build_headers(request: Request) -> dict:
    """
    Build upstream headers:

    - Always set Authorization from our relay's OPENAI_API_KEY.
    - Optionally add OpenAI-Organization from OPENAI_ORG_ID.
    - Propagate or override OpenAI-Beta, favoring env if set.
    - Forward Idempotency-Key if present.
    """
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not configured")

    headers: dict[str, str] = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "User-Agent": USER_AGENT,
        "Content-Type": "application/json",
    }

    if OPENAI_ORG_ID:
        headers["OpenAI-Organization"] = OPENAI_ORG_ID

    # Merge beta headers: env wins, otherwise propagate client header
    beta_from_env = OPENAI_RESPONSES_BETA.strip()
    beta_from_client = request.headers.get("OpenAI-Beta", "").strip()
    beta_header = beta_from_env or beta_from_client
    if beta_header:
        headers["OpenAI-Beta"] = beta_header

    idem = request.headers.get("Idempotency-Key")
    if idem:
        headers["Idempotency-Key"] = idem

    return headers


async def _stream_responses(
    client: httpx.AsyncClient,
    request: Request,
    body: dict,
) -> AsyncGenerator[bytes, None]:
    """
    Stream Server-Sent Events (SSE) from OpenAI's /v1/responses endpoint
    back to the caller unchanged.
    """
    url = _base_url("/v1/responses")

    async with client.stream(
        "POST",
        url,
        headers=build_headers(request),
        content=json.dumps(body),
        timeout=None,  # streaming; let upstream control timeouts
    ) as upstream:
        async for chunk in upstream.aiter_bytes():
            # Pass through raw SSE data
            yield chunk


@router.post("/responses")
async def create_response(request: Request) -> StreamingResponse | JSONResponse:
    """
    Proxy POST /v1/responses with optional streaming support.

    This matches openai-python 2.8 / openai-node 6.9 `responses.create(...)`
    semantics, including `stream: true` for SSE.

    Optional micro-tweak:
    - If the client sends Accept: text/event-stream, we also treat this as a
      request for streaming, even if the JSON body does not explicitly include
      "stream": true. This makes the relay friendlier to non-SDK clients that
      negotiate streaming via the Accept header.
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

    async with httpx.AsyncClient(timeout=RELAY_TIMEOUT) as client:
        if should_stream:
            generator = _stream_responses(client, request, body)
            return StreamingResponse(
                generator,
                media_type="text/event-stream",
            )

        url = _base_url("/v1/responses")
        upstream = await client.post(
            url,
            headers=build_headers(request),
            content=json.dumps(body),
        )

    if upstream.is_error:
        # Bubble up OpenAI error payload directly
        raise HTTPException(
            status_code=upstream.status_code,
            detail=upstream.text,
        )

    return JSONResponse(
        status_code=upstream.status_code,
        content=upstream.json(),
    )


@router.get("/responses/{response_id}")
async def retrieve_response(response_id: str, request: Request) -> JSONResponse:
    """
    Proxy GET /v1/responses/{id}.
    """
    async with httpx.AsyncClient(timeout=RELAY_TIMEOUT) as client:
        url = _base_url(f"/v1/responses/{response_id}")
        upstream = await client.get(url, headers=build_headers(request))

    if upstream.is_error:
        raise HTTPException(
            status_code=upstream.status_code,
            detail=upstream.text,
        )

    return JSONResponse(
        status_code=upstream.status_code,
        content=upstream.json(),
    )
