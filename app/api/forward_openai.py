from __future__ import annotations

import json
import os
from typing import Any, Dict, Iterable

import httpx
from fastapi import HTTPException, Request, Response

from app.utils.logger import relay_log as logger


def _get_openai_base() -> str:
    """
    Resolve the upstream OpenAI base URL.

    Defaults to the public OpenAI REST API if not overridden.
    """
    base = os.getenv("OPENAI_API_BASE", "https://api.openai.com").strip()
    if base.endswith("/"):
        base = base[:-1]
    return base


def _build_upstream_headers(incoming: Iterable[tuple[str, str]]) -> Dict[str, str]:
    """
    Build the headers to send to OpenAI.

    - Always attach Authorization from OPENAI_API_KEY.
    - Attach OpenAI-Organization from incoming header or OPENAI_ORG env.
    - Pass through OpenAI-* headers (beta / experimental flags).
    """
    headers: Dict[str, str] = {}

    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_TOKEN")
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    env_org = os.getenv("OPENAI_ORG") or os.getenv("OPENAI_ORGANIZATION")

    for name, value in incoming:
        lower = name.lower()
        if lower == "authorization":
            # We prefer the server-side key rather than trusting the client.
            continue
        if lower in ("host", "content-length", "connection"):
            continue
        if lower == "openai-organization":
            headers["OpenAI-Organization"] = value
            continue
        if lower.startswith("openai-"):
            # Pass through OpenAI-Beta, OpenAI-Experimental, etc.
            headers[name] = value

    if "OpenAI-Organization" not in headers and env_org:
        headers["OpenAI-Organization"] = env_org

    return headers


def _filter_response_headers(upstream: httpx.Headers) -> Dict[str, str]:
    """
    Select which headers from OpenAI to propagate back to the client.

    We avoid hop-by-hop headers and let ASGI / FastAPI handle transfer
    encoding, connection management, etc.
    """
    allowed_prefixes = ("openai-", "x-", "cf-")
    allowed_exact = {"content-type"}

    result: Dict[str, str] = {}
    for name, value in upstream.items():
        lower = name.lower()
        if lower in ("content-length", "connection", "transfer-encoding"):
            continue
        if lower in allowed_exact or lower.startswith(allowed_prefixes):
            result[name] = value
    return result


async def forward_openai_request(
    request: Request,
    *,
    upstream_path: str | None = None,
    upstream_method: str | None = None,
) -> Response:
    """
    Generic forwarder for OpenAI-style /v1/* requests.

    Used by all the thin routers (models, files, images, videos, embeddings,
    responses, etc.) so behavior stays aligned with the official REST spec
    and the openai-python 2.8.x client.

    This function:
      - Builds the full upstream URL from OPENAI_API_BASE + request path
      - Copies query params from the incoming request
      - Detects JSON bodies and uses `json=...` for httpx so pytest_httpx
        can expose Request.json() in tests
      - Proxies status code, body, and key headers back to the caller
    """
    method = (upstream_method or request.method).upper()
    path = upstream_path or request.url.path

    base_url = _get_openai_base()
    target_url = f"{base_url}{path}"

    # Query parameters
    params: Dict[str, Any] = dict(request.query_params)

    # Incoming headers and body
    raw_body: bytes = await request.body()
    content_type = request.headers.get("content-type", "").lower()

    # Detect JSON body where possible so that pytest_httpx's Request objects
    # expose a .json() for the smoke tests.
    json_data: Any | None = None
    if raw_body and "application/json" in content_type:
        try:
            json_data = json.loads(raw_body.decode("utf-8"))
        except Exception:
            json_data = None

    # Build upstream headers
    upstream_headers = _build_upstream_headers(request.headers.items())

    # Prepare request kwargs for httpx
    request_kwargs: Dict[str, Any] = {}
    if json_data is not None:
        request_kwargs["json"] = json_data
    elif raw_body:
        # Non-JSON body (e.g. multipart/form-data or binary download)
        request_kwargs["content"] = raw_body

    logger.info("forward_openai_request.start method=%s path=%s", method, path)

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            upstream_resp = await client.request(
                method=method,
                url=target_url,
                params=params,
                headers=upstream_headers,
                **request_kwargs,
            )
    except httpx.RequestError as exc:
        logger.warning("forward_openai_request.error %s", exc)
        raise HTTPException(
            status_code=502,
            detail={
                "error": {
                    "message": "Error contacting upstream OpenAI API",
                    "type": "upstream_connection_error",
                }
            },
        ) from exc

    logger.info(
        "forward_openai_request.done method=%s path=%s status=%s",
        method,
        path,
        upstream_resp.status_code,
    )

    response_headers = _filter_response_headers(upstream_resp.headers)

    return Response(
        content=upstream_resp.content,
        status_code=upstream_resp.status_code,
        headers=response_headers,
    )
