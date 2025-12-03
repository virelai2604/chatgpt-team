# app/routes/containers.py

from __future__ import annotations

from fastapi import APIRouter, Request

from app.api.forward_openai import forward_openai_request

router = APIRouter(tags=["containers"])


@router.post("/v1/containers")
async def create_container(request: Request):
    """
    Proxy for: POST https://api.openai.com/v1/containers
    """
    return await forward_openai_request(request)


@router.get("/v1/containers")
async def list_containers(request: Request):
    """
    Proxy for: GET https://api.openai.com/v1/containers
    """
    return await forward_openai_request(request)


@router.get("/v1/containers/{container_id}")
async def retrieve_container(request: Request, container_id: str):
    """
    Proxy for: GET https://api.openai.com/v1/containers/{container_id}
    """
    return await forward_openai_request(request)


@router.delete("/v1/containers/{container_id}")
async def delete_container(request: Request, container_id: str):
    """
    Proxy for: DELETE https://api.openai.com/v1/containers/{container_id}
    """
    return await forward_openai_request(request)


@router.post("/v1/containers/{container_id}/files")
async def upload_container_file(request: Request, container_id: str):
    """
    Proxy for: POST https://api.openai.com/v1/containers/{container_id}/files
    """
    return await forward_openai_request(request)


@router.get("/v1/containers/{container_id}/files")
async def list_container_files(request: Request, container_id: str):
    """
    Proxy for: GET https://api.openai.com/v1/containers/{container_id}/files
    """
    return await forward_openai_request(request)


@router.get("/v1/containers/{container_id}/files/{file_id}/content")
async def get_container_file_content(request: Request, container_id: str, file_id: str):
    """
    Proxy for:
      GET https://api.openai.com/v1/containers/{container_id}/files/{file_id}/content
    """
    return await forward_openai_request(request)


@router.delete("/v1/containers/{container_id}/files/{file_id}")
async def delete_container_file(request: Request, container_id: str, file_id: str):
    """
    Proxy for:
      DELETE https://api.openai.com/v1/containers/{container_id}/files/{file_id}
    """
    return await forward_openai_request(request)
