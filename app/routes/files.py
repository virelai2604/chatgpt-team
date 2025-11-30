# app/routes/files.py
from __future__ import annotations

from fastapi import APIRouter, Request, Response

from app.api.forward_openai import forward_openai_request

router = APIRouter(
    tags=["files"],
)


@router.get("/v1/files")
async def list_files(request: Request) -> Response:
    return await forward_openai_request(request)


@router.post("/v1/files")
async def create_file(request: Request) -> Response:
    return await forward_openai_request(request)


@router.get("/v1/files/{file_id}")
async def retrieve_file(file_id: str, request: Request) -> Response:
    return await forward_openai_request(request)


@router.delete("/v1/files/{file_id}")
async def delete_file(file_id: str, request: Request) -> Response:
    return await forward_openai_request(request)
