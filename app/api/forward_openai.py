# app/api/forward_openai.py
from typing import Dict

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import Response

from ..core.config import get_settings
from ..utils.logger import get_logger

router = APIRouter(prefix="/v1", tags=["openai"])

_settings = get_settings()
logger = get_logger(__name__)


async def _forward_to_openai(request: Request, path: str) -> Response:
    url = f"{_settings.openai_base_url.rstrip('/')}/{path}"

    params: Dict[str, str] = dict(request.query_params)

    # Copy headers but drop hop-by-hop headers and host/content-length
    incoming_headers = dict(request.headers)
    for hop in (
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
    ):
        incoming_headers.pop(hop, None)

    headers = {
        **incoming_headers,
        "Authorization": f"Bearer {_settings.openai_api_key}",
    }

    if _settings.openai_organization:
        headers["OpenAI-Organization"] = _settings.openai_organization

    body = await request.body()

    async with httpx.AsyncClient(timeout=_settings.timeout_seconds) as client:
        upstream = await client.request(
            method=request.method,
            url=url,
            params=params,
            headers=headers,
            content=body or None,
        )

    logger.debug(
        "Forwarded request to OpenAI",
        extra={"method": request.method, "path": path, "status_code": upstream.status_code},
    )

    # Filter response headers to avoid conflicts
    response_headers = {
        k: v
        for k, v in upstream.headers.items()
        if k.lower() in {"content-type", "cache-control"}
    }

    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        headers=response_headers,
        media_type=upstream.headers.get("content-type"),
    )


@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def forward_openai(path: str, request: Request) -> Response:
    """
    Generic pass-through for OpenAI's REST API under /v1/*.
    """
    return await _forward_to_openai(request, path)
