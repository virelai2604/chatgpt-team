# app/routes/containers.py

from __future__ import annotations

from fastapi import APIRouter, Request, Response

from app.api.forward_openai import forward_openai_request

router = APIRouter(
    prefix="/v1",
    tags=["containers"],
)


@router.post("/containers")
async def create_container(request: Request) -> Response:
    return await forward_openai_request(request)


@router.get("/containers")
async def list_containers(request: Request) -> Response:
    return await forward_openai_request(request)


@router.get("/containers/{container_id}")
async def retrieve_container(container_id: str, request: Request) -> Response:
    return await forward_openai_request(request)


@router.delete("/containers/{container_id}")
async def delete_container(container_id: str, request: Request) -> Response:
    return await forward_openai_request(request)


@router.get("/containers/{container_id}/files")
async def list_container_files(container_id: str, request: Request) -> Response:
    return await forward_openai_request(request)


@router.get("/containers/{container_id}/files/{file_id}")
async def retrieve_container_file(
    container_id: str,
    file_id: str,
    request: Request,
) -> Response:
    return await forward_openai_request(request)


@router.get("/containers/{container_id}/files/{file_id}/content")
async def download_container_file_content(
    container_id: str,
    file_id: str,
    request: Request,
) -> Response:
    return await forward_openai_request(request)
