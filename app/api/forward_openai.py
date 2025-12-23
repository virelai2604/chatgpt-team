from __future__ import annotations

import json
from typing import Any, Dict, Mapping, Optional
from urllib.parse import urlencode

import httpx
from fastapi import Request
from fastapi.responses import Response, StreamingResponse

from app.core.config import settings
from app.core.http_client import get_async_httpx_client, get_async_openai_client


_HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
    "host",
    "content-length",
}


def _get_setting(*names: str, default=None):
    for name in names:
        if hasattr(settings, name):
            val = getattr(settings, name)
            if val is not None:
                return val
    return default


def _openai_base_url() -> str:
    return str(
        _get_setting(
            "OPENAI_BASE_URL",
            "OPENAI_API_BASE",
            "openai_base_url",
            "openai_api_base",
            default="https://api.openai.com/v1",
        )
    ).rstrip("/")


def _openai_api_key() -> str:
    key = _get_setting("OPENAI_API_KEY", "openai_api_key")
    if not key:
        raise RuntimeError("OPENAI_API_KEY is not configured.")
    return str(key)


def _join_url(base: str, path: str) -> str:
    base = base.rstrip("/")
    path = "/" + path.lstrip("/")
    # Avoid /v1/v1 duplication
    if base.endswith("/v1") and path.startswith("/v1/"):
        path = path[len("/v1") :]
    return base + path


def _filter_outgoing_headers(in_headers: Mapping[str, str]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for k, v in in_headers.items():
        lk = k.lower()
        if lk in _HOP_BY_HOP_HEADERS:
            continue
        if lk == "authorization":
            # Never forward client auth upstream.
            continue
        out[k] = v

    # Force upstream OpenAI key.
    out["Authorization"] = f"Bearer {_openai_api_key()}"

    # Optional org/project headers if you use them via config.
    org = _get_setting("OPENAI_ORG", "OPENAI_ORGANIZATION")
    if org:
        out["OpenAI-Organization"] = str(org)

    project = _get_setting("OPENAI_PROJECT", "openai_project")
    if project:
        out["OpenAI-Project"] = str(project)

    return out


def _filter_incoming_headers(up_headers: httpx.Headers) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for k, v in up_headers.items():
        lk = k.lower()
        if lk in _HOP_BY_HOP_HEADERS:
            continue
        # Let Starlette set content-length.
        out[k] = v
    return out


def _maybe_model_dump(obj: Any) -> Any:
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if hasattr(obj, "dict"):
        return obj.dict()
    return obj


async def forward_openai_request(request: Request) -> Response:
    """
    Raw HTTP passthrough for endpoints that are better forwarded than modeled.
    Supports SSE streaming if upstream returns text/event-stream.
    """
    base = _openai_base_url()
    upstream_url = _join_url(base, request.url.path)

    if request.url.query:
        upstream_url = upstream_url + "?" + request.url.query

    headers = _filter_outgoing_headers(request.headers)

    body_bytes: Optional[bytes]
    if request.method.upper() in {"GET", "HEAD"}:
        body_bytes = None
    else:
        body_bytes = await request.body()

    client = get_async_httpx_client()
    req = client.build_request(
        method=request.method.upper(),
        url=upstream_url,
        headers=headers,
        content=body_bytes,
    )

    resp = await client.send(req, stream=True)
    media_type = resp.headers.get("content-type")

    if media_type and "text/event-stream" in media_type.lower():
        async def gen():
            try:
                async for chunk in resp.aiter_raw():
                    yield chunk
            finally:
                await resp.aclose()

        return StreamingResponse(
            gen(),
            status_code=resp.status_code,
            headers=_filter_incoming_headers(resp.headers),
            media_type=media_type,
        )

    data = await resp.aread()
    await resp.aclose()
    return Response(
        content=data,
        status_code=resp.status_code,
        headers=_filter_incoming_headers(resp.headers),
        media_type=media_type,
    )


async def forward_openai_method_path(
    *,
    request: Request,
    method: str,
    path: str,
    query: Optional[Mapping[str, Any]] = None,
    body: Optional[Any] = None,
) -> Response:
    """
    JSON-focused forwarder used by the generic /v1/proxy envelope.
    """
    base = _openai_base_url()
    url = _join_url(base, path)

    if query:
        url = url + "?" + urlencode(query, doseq=True)

    headers = _filter_outgoing_headers(request.headers)

    content: Optional[bytes] = None
    if method.upper() not in {"GET", "HEAD"}:
        if body is None:
            content = None
        elif isinstance(body, (bytes, bytearray)):
            content = bytes(body)
        else:
            content = json.dumps(body).encode("utf-8")
            headers.setdefault("Content-Type", "application/json")

    client = get_async_httpx_client()
    resp = await client.request(method.upper(), url, headers=headers, content=content)

    return Response(
        content=resp.content,
        status_code=resp.status_code,
        headers=_filter_incoming_headers(resp.headers),
        media_type=resp.headers.get("content-type"),
    )


# --- Typed helpers used by routers ---

async def forward_responses_create(payload: Dict[str, Any]) -> Any:
    """
    Uses openai-python for non-streaming /v1/responses calls.
    Your /v1/responses router expects this symbol to exist.:contentReference[oaicite:6]{index=6}
    """
    client = get_async_openai_client()
    result = await client.responses.create(**payload)
    return _maybe_model_dump(result)


async def forward_embeddings_create(payload: Dict[str, Any]) -> Any:
    client = get_async_openai_client()
    result = await client.embeddings.create(**payload)
    return _maybe_model_dump(result)
