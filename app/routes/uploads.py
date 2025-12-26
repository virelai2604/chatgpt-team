from __future__ import annotations

from fastapi import APIRouter, Request, Response

from app.api.forward_openai import forward_openai_request

router = APIRouter(prefix="/v1", tags=["uploads"])


@router.post("/uploads")
async def create_upload(request: Request) -> Response:
    return await forward_openai_request(request)


@router.post("/uploads/{upload_id}/parts")
async def create_upload_part(upload_id: str, request: Request) -> Response:
    return await forward_openai_request(request)


@router.post("/uploads/{upload_id}/complete")
async def complete_upload(upload_id: str, request: Request) -> Response:
    return await forward_openai_request(request)


@router.post("/uploads/{upload_id}/cancel")
async def cancel_upload(upload_id: str, request: Request) -> Response:
    return await forward_openai_request(request)


@router.api_route(
    "/uploads/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    include_in_schema=False,
)
async def uploads_passthrough(path: str, request: Request) -> Response:
    upstream_path = f"/v1/uploads/{path}".rstrip("/")
    return await forward_openai_request(request, upstream_path=upstream_path)
