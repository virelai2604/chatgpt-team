from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import Response

from app.api.forward_openai import forward_openai_request

router = APIRouter(prefix="/v1", tags=["uploads"])


@router.post("/uploads")
async def uploads_create(request: Request) -> Response:
    # POST /v1/uploads
    return await forward_openai_request(request, upstream_path="/v1/uploads")


@router.post("/uploads/{upload_id}/parts")
async def uploads_add_part(upload_id: str, request: Request) -> Response:
    # POST /v1/uploads/{upload_id}/parts
    return await forward_openai_request(request, upstream_path=f"/v1/uploads/{upload_id}/parts")


@router.post("/uploads/{upload_id}/complete")
async def uploads_complete(upload_id: str, request: Request) -> Response:
    # POST /v1/uploads/{upload_id}/complete
    return await forward_openai_request(request, upstream_path=f"/v1/uploads/{upload_id}/complete")


@router.post("/uploads/{upload_id}/cancel")
async def uploads_cancel(upload_id: str, request: Request) -> Response:
    # POST /v1/uploads/{upload_id}/cancel
    return await forward_openai_request(request, upstream_path=f"/v1/uploads/{upload_id}/cancel")


@router.api_route(
    "/uploads/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    include_in_schema=False,
)
async def uploads_passthrough(path: str, request: Request) -> Response:
    """
    Hidden escape hatch for new or less-common uploads routes.

    We keep it out of OpenAPI to avoid:
      - clutter
      - operationId collisions in composed schemas
    """
    return await forward_openai_request(request, upstream_path=f"/v1/uploads/{path}")
