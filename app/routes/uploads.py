from __future__ import annotations

import asyncio
import json
from typing import Optional

from fastapi import APIRouter, Request
from fastapi.responses import Response

from app.api.forward_openai import forward_openai_method_path, forward_openai_request

router = APIRouter(prefix="/v1", tags=["uploads"])


def _safe_json_from_response(resp: Response) -> Optional[dict]:
    """
    Best-effort JSON parse for a Starlette/FastAPI Response created with `content=bytes`.
    """
    try:
        body = getattr(resp, "body", None)
        if not body:
            return None
        if isinstance(body, (bytes, bytearray)):
            return json.loads(bytes(body).decode("utf-8"))
        if isinstance(body, str):
            return json.loads(body)
    except Exception:
        return None
    return None


async def _forward_complete_with_retries(request: Request, upload_id: str) -> Response:
    """
    Upload completion has occasionally surfaced transient upstream 5xx errors.
    Since completion is effectively idempotent for a given upload_id, we retry a few times,
    and finally fall back to GET /uploads/{upload_id} if completion appears to have succeeded.
    """
    delays = [0.0, 0.25, 0.75, 1.5]  # seconds (bounded; keeps tests reasonable)
    last: Optional[Response] = None

    for delay in delays:
        if delay:
            await asyncio.sleep(delay)

        resp = await forward_openai_request(request)
        last = resp

        # Any non-5xx we return immediately (includes 2xx, 4xx, etc).
        if resp.status_code < 500:
            return resp

    # Fallback: check the upload status (sometimes upstream completed but the response was 5xx).
    check = await forward_openai_method_path(
        method="GET",
        path=f"/v1/uploads/{upload_id}",
        inbound_headers=request.headers,
    )

    if check.status_code == 200:
        data = _safe_json_from_response(check)
        if isinstance(data, dict):
            status = data.get("status")
            file_obj = data.get("file")
            file_id = file_obj.get("id") if isinstance(file_obj, dict) else None
            if status == "completed" and isinstance(file_id, str) and file_id.startswith("file-"):
                return check

    # Give up and return the last completion attempt.
    return last or check


# Explicit complete endpoint with retries/fallback.
@router.post("/uploads/{upload_id}/complete", summary="Complete an upload (with retries)")
async def uploads_complete(upload_id: str, request: Request) -> Response:
    return await _forward_complete_with_retries(request, upload_id)


# The rest of the uploads API is raw passthrough.
@router.api_route("/uploads", methods=["POST"], summary="Create an upload")
async def uploads_create(request: Request) -> Response:
    return await forward_openai_request(request)


@router.api_route("/uploads/{path:path}", methods=["GET", "POST", "DELETE"], summary="Uploads passthrough")
async def uploads_passthrough(request: Request) -> Response:
    return await forward_openai_request(request)
