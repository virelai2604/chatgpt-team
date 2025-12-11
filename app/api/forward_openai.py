# app/api/forward_openai.py

from __future__ import annotations

import json
from typing import Any, AsyncIterator, Dict, Optional
from urllib.parse import urljoin

import httpx
from fastapi import Request, Response
from fastapi.responses import StreamingResponse

from app.core.config import settings
from app.core.http_client import get_async_openai_client
from app.utils.logger import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Helpers for working with the typed OpenAI SDK
# ---------------------------------------------------------------------------


def _to_plain(result: Any) -> Any:
    """
    Convert pydantic / OpenAI SDK objects to plain JSON-serializable Python
    structures for returning in FastAPI responses.
    """
    if hasattr(result, "model_dump_json"):
        # OpenAI SDK 2.x models
        return json.loads(result.model_dump_json())
    if hasattr(result, "model_dump"):
        return result.model_dump()
    return result


async def forward_responses_create(payload: Dict[str, Any]) -> Any:
    """
    Forward to OpenAI Responses API.

    Non-streaming:
        client.responses.create(**payload)

    Streaming:
        client.responses.create(stream=True, event_handler=...)
    """
    client = get_async_openai_client()
    logger.debug("Forwarding /v1/responses payload: %s", payload)
    result = await client.responses.create(**payload)
    return _to_plain(result)


async def forward_responses_create_streaming(
    payload: Dict[str, Any],
) -> AsyncIterator[Any]:
    """
    Forward a streaming Responses.create(**payload, stream=True) call.

    Returns an async iterator of event objects. The routes layer is responsible
    for translating those into SSE bytes.
    """
    client = get_async_openai_client()
    logger.debug("Forwarding /v1/responses (streaming) payload: %s", payload)

    # Ensure stream=True
    payload = dict(payload)
    payload["stream"] = True

    # The SDK returns an async iterator of events
    async with client.responses.stream(**payload) as stream:
        async for event in stream:
            yield event


async def forward_responses_compact(payload: Dict[str, Any]) -> Any:
    """
    Forward to OpenAI Responses compact endpoint:

        POST https://api.openai.com/v1/responses/compact

    Python SDK equivalent:

        client.responses.compact(**payload)

    Requires openai-python 2.10.0+ (Responses.compact is part of the
    modern Responses API surface).
    """
    client = get_async_openai_client()
    logger.debug("Forwarding /v1/responses/compact payload: %s", payload)
    result = await client.responses.compact(**payload)
    return _to_plain(result)


async def forward_embeddings_create(payload: Dict[str, Any]) -> Any:
    """
    Typed helper for /v1/embeddings.

    Equivalent to:
        client.embeddings.create(**payload)
    """
    client = get_async_openai_client()
    logger.debug("Forwarding /v1/embeddings payload: %s", payload)
    result = await client.embeddings.create(**payload)
    return _to_plain(result)


async def forward_models_list() -> Any:
    """
    Typed helper for listing models via the SDK.

    Equivalent to:
        client.models.list()
    """
    client = get_async_openai_client()
    logger.debug("Forwarding /v1/models list request")
    result = await client.models.list()
    return _to_plain(result)


async def forward_models_retrieve(model_id: str) -> Any:
    """
    Typed helper for retrieving a single model.

    Equivalent to:
        client.models.retrieve(model_id)
    """
    client = get_async_openai_client()
    logger.debug("Forwarding /v1/models/%s retrieve request", model_id)
    result = await client.models.retrieve(model_id)
    return _to_plain(result)


# ---------------------------------------------------------------------------
# Generic raw HTTP forwarder for any other /v1/* path
# ---------------------------------------------------------------------------


async def _do_forward(
    method: str,
    path: str,
    request: Request,
    stream: bool = False,
) -> Response:
    """
    Generic forwarding logic used by forward_openai_request.

    - Builds the upstream URL by joining OPENAI_API_BASE (or default) with `path`
    - Preserves method, headers (minus hop-by-hop), query params, and body
    - Returns either a normal Response or a StreamingResponse.
    """
    # Base URL for upstream, e.g. https://api.openai.com/v1/
    base_url = str(settings.OPENAI_API_BASE).rstrip("/") + "/"
    url = urljoin(base_url, path.lstrip("/"))
    logger.debug("Forwarding generic request to OpenAI: %s %s", method, url)

    # Read incoming body once
    body = await request.body()

    # Copy headers, but strip ones that should not be proxied as-is
    excluded_headers = {
        "host",
        "content-length",
        "connection",
        "keep-alive",
        "proxy-authenticate",
        "proxy-authorization",
        "te",
        "trailers",
        "transfer-encoding",
        "upgrade",
    }
    headers = {
        k: v
        for k, v in request.headers.items()
        if k.lower() not in excluded_headers
    }

    async with httpx.AsyncClient(timeout=None) as client:
        if stream:
            upstream = client.stream(
                method,
                url,
                headers=headers,
                params=request.query_params,
                content=body,
            )
            return StreamingResponse(
                _do_stream(upstream),
                status_code=200,
                media_type="text/event-stream",
            )

        resp = await client.request(
            method,
            url,
            headers=headers,
            params=request.query_params,
            content=body,
        )

    return Response(
        content=resp.content,
        status_code=resp.status_code,
        headers=dict(resp.headers),
        media_type=resp.headers.get("content-type"),
    )


async def _do_stream(upstream: httpx._client.AsyncClient.stream) -> AsyncIterator[bytes]:
    """
    Relay upstream streaming response chunks as-is.
    """
    async with upstream as response:
        async for chunk in response.aiter_bytes():
            yield chunk


def _extract_upstream_path(request: Request) -> str:
    """
    Map the inbound path to the corresponding upstream path under /v1.

    For now we assume the relay itself is mounted at '/', so the path already
    begins with '/v1/...'. If you mount under a sub-path, adjust here.
    """
    path = request.url.path

    # Simple case: path already starts with /v1
    if path.startswith("/v1/"):
        return path.lstrip("/")

    # If someone hits e.g. /chat/completions, normalize to /v1/chat/completions
    if path.startswith("/"):
        return f"v1{path}"
    return f"v1/{path}"


async def forward_openai_request(request: Request, stream: bool = False) -> Response:
    """
    Generic proxy entrypoint used by the legacy routes (chat completions, etc.).

    Most new work should prefer the typed helpers and purpose-built routes
    instead of this catch-all, but it remains useful for backwards compatibility
    and for endpoints we haven't added typed wrappers for yet.
    """
    upstream_path = _extract_upstream_path(request)
    logger.info(
        "Generic OpenAI forward: %s %s (stream=%s)",
        request.method,
        upstream_path,
        stream,
    )
    return await _do_forward(
        method=request.method,
        path=upstream_path,
        request=request,
        stream=stream,
    )
