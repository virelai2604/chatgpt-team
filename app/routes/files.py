from __future__ import annotations

from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, Response, StreamingResponse
from starlette.background import BackgroundTask

from app.api.forward_openai import (
    build_outbound_headers,
    build_upstream_url,
    filter_upstream_headers,
    forward_openai_request,
    forward_files_create,
    forward_files_delete,
    forward_files_list,
    forward_files_retrieve,
)
from app.core.http_client import get_async_httpx_client
from app.utils.logger import relay_log

# Compatibility: support either `get_settings()` or a module-level `settings`
try:
    from app.core.config import get_settings  # type: ignore
except ImportError:  # pragma: no cover
    from app.core.config import settings as _settings  # type: ignore

    def get_settings():  # type: ignore
        return _settings

router = APIRouter(prefix="/v1", tags=["files"])


def _timeout_seconds() -> float:
    settings = get_settings()
    for attr in ("proxy_timeout_seconds", "PROXY_TIMEOUT", "HTTP_TIMEOUT_SECONDS", "RELAY_TIMEOUT", "timeout_seconds"):
        if hasattr(settings, attr):
            try:
                val = float(getattr(settings, attr))
                if val > 0:
                    return val
            except Exception:
                continue
    return 90.0


@router.get("/files")
async def list_files(purpose: Optional[str] = None) -> JSONResponse:
    resp = await forward_files_list(purpose=purpose)
    payload = resp.model_dump() if hasattr(resp, "model_dump") else resp
    return JSONResponse(content=payload)


@router.post("/files")
async def create_file(request: Request) -> JSONResponse:
    form = await request.form()
    up = form.get("file")
    purpose = form.get("purpose")
    if up is None:
        raise HTTPException(status_code=400, detail="Missing multipart field: file")
    if not purpose:
        raise HTTPException(status_code=400, detail="Missing multipart field: purpose")

    resp = await forward_files_create(file=up, purpose=str(purpose))
    payload = resp.model_dump() if hasattr(resp, "model_dump") else resp
    return JSONResponse(content=payload)


@router.get("/files/{file_id}")
async def retrieve_file(file_id: str) -> JSONResponse:
    resp = await forward_files_retrieve(file_id)
    payload = resp.model_dump() if hasattr(resp, "model_dump") else resp
    return JSONResponse(content=payload)


@router.delete("/files/{file_id}")
async def delete_file(file_id: str) -> JSONResponse:
    resp = await forward_files_delete(file_id)
    payload = resp.model_dump() if hasattr(resp, "model_dump") else resp
    return JSONResponse(content=payload)


@router.api_route("/files/{file_id}/content", methods=["GET", "HEAD"])
async def retrieve_file_content(file_id: str, request: Request) -> Response:
    """
    Stream file bytes from upstream (GET) and support curl -I (HEAD).

    For HEAD we perform a minimal ranged GET (bytes=0-0) to surface headers without
    downloading the full file.
    """
    upstream_path = f"/v1/files/{file_id}/content"
    upstream_url = build_upstream_url(upstream_path)

    headers = build_outbound_headers(
        inbound_headers=request.headers,
        content_type=None,
        forward_accept=False,
        path_hint=upstream_path,
    )

    if request.headers.get("range"):
        headers["Range"] = request.headers["range"]

    client = get_async_httpx_client()
    timeout = _timeout_seconds()

    if request.method == "HEAD":
        if "Range" not in headers:
            headers["Range"] = "bytes=0-0"

        upstream_req = client.build_request(
            "GET",
            upstream_url,
            params=request.query_params,
            headers=headers,
        )
        try:
            upstream_resp = await client.send(upstream_req, stream=True, timeout=timeout)
        except httpx.TimeoutException as exc:
            raise HTTPException(status_code=504, detail=f"Upstream timeout fetching headers: {type(exc).__name__}: {exc}") from exc
        except httpx.RequestError as exc:
            raise HTTPException(status_code=502, detail=f"Upstream request failed fetching headers: {type(exc).__name__}: {exc}") from exc

        await upstream_resp.aclose()
        return Response(
            content=b"",
            status_code=upstream_resp.status_code,
            headers=filter_upstream_headers(upstream_resp.headers),
            media_type=upstream_resp.headers.get("content-type"),
        )

    upstream_req = client.build_request(
        "GET",
        upstream_url,
        params=request.query_params,
        headers=headers,
    )

    try:
        upstream_resp = await client.send(upstream_req, stream=True, timeout=timeout)
    except httpx.TimeoutException as exc:
        raise HTTPException(status_code=504, detail=f"Upstream timeout downloading file: {type(exc).__name__}: {exc}") from exc
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail=f"Upstream request failed downloading file: {type(exc).__name__}: {exc}") from exc

    if upstream_resp.status_code >= 400:
        body = await upstream_resp.aread()
        headers_out = filter_upstream_headers(upstream_resp.headers)
        await upstream_resp.aclose()
        return Response(
            content=body,
            status_code=upstream_resp.status_code,
            headers=headers_out,
            media_type=upstream_resp.headers.get("content-type"),
        )

    async def iter_bytes():
        async for chunk in upstream_resp.aiter_bytes():
            yield chunk

    return StreamingResponse(
        iter_bytes(),
        status_code=upstream_resp.status_code,
        headers=filter_upstream_headers(upstream_resp.headers),
        media_type=upstream_resp.headers.get("content-type"),
        background=BackgroundTask(upstream_resp.aclose),
    )


@router.api_route("/files/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD"], include_in_schema=False)
async def files_passthrough(request: Request, path: str) -> Response:
    relay_log.debug("files passthrough -> %s", path)
    return await forward_openai_request(request)
