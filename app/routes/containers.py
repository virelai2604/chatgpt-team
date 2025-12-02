# app/routes/containers.py

from __future__ import annotations

from fastapi import APIRouter, Request, Response

from app.api.forward_openai import forward_openai_request
from app.utils.logger import relay_log as logger

router = APIRouter(prefix="/v1", tags=["containers"])


# ---------------------------------------------------------------------------
# Containers root
# ---------------------------------------------------------------------------


@router.post("/containers")
async def create_container(request: Request) -> Response:
    """
    Thin proxy:
    POST https://api.openai.com/v1/containers
    """
    logger.info(
        "Relay: create container",
        extra={"path": "/v1/containers", "method": "POST"},
    )
    return await forward_openai_request(request)


@router.get("/containers")
async def list_containers(request: Request) -> Response:
    """
    Thin proxy:
    GET https://api.openai.com/v1/containers
    """
    logger.info(
        "Relay: list containers",
        extra={"path": "/v1/containers", "method": "GET"},
    )
    return await forward_openai_request(request)


@router.get("/containers/{container_id}")
async def retrieve_container(container_id: str, request: Request) -> Response:
    """
    Thin proxy:
    GET https://api.openai.com/v1/containers/{container_id}
    """
    logger.info(
        "Relay: retrieve container",
        extra={"path": f"/v1/containers/{container_id}", "method": "GET"},
    )
    return await forward_openai_request(request)


@router.delete("/containers/{container_id}")
async def delete_container(container_id: str, request: Request) -> Response:
    """
    Thin proxy:
    DELETE https://api.openai.com/v1/containers/{container_id}
    """
    logger.info(
        "Relay: delete container",
        extra={"path": f"/v1/containers/{container_id}", "method": "DELETE"},
    )
    return await forward_openai_request(request)


# ---------------------------------------------------------------------------
# Container files
# ---------------------------------------------------------------------------


@router.post("/containers/{container_id}/files")
async def create_container_file(container_id: str, request: Request) -> Response:
    """
    Thin proxy:
    POST https://api.openai.com/v1/containers/{container_id}/files
    """
    logger.info(
        "Relay: create container file",
        extra={
            "path": f"/v1/containers/{container_id}/files",
            "method": "POST",
        },
    )
    return await forward_openai_request(request)


@router.get("/containers/{container_id}/files")
async def list_container_files(container_id: str, request: Request) -> Response:
    """
    Thin proxy:
    GET https://api.openai.com/v1/containers/{container_id}/files
    """
    logger.info(
        "Relay: list container files",
        extra={
            "path": f"/v1/containers/{container_id}/files",
            "method": "GET",
        },
    )
    return await forward_openai_request(request)


@router.get("/containers/{container_id}/files/{file_id}")
async def retrieve_container_file(
    container_id: str,
    file_id: str,
    request: Request,
) -> Response:
    """
    Thin proxy:
    GET https://api.openai.com/v1/containers/{container_id}/files/{file_id}
    """
    logger.info(
        "Relay: retrieve container file",
        extra={
            "path": f"/v1/containers/{container_id}/files/{file_id}",
            "method": "GET",
        },
    )
    return await forward_openai_request(request)


@router.get("/containers/{container_id}/files/{file_id}/content")
async def get_container_file_content(
    container_id: str,
    file_id: str,
    request: Request,
) -> Response:
    """
    Thin proxy:
    GET https://api.openai.com/v1/containers/{container_id}/files/{file_id}/content
    """
    logger.info(
        "Relay: get container file content",
        extra={
            "path": f"/v1/containers/{container_id}/files/{file_id}/content",
            "method": "GET",
        },
    )
    return await forward_openai_request(request)


@router.delete("/containers/{container_id}/files/{file_id}")
async def delete_container_file(
    container_id: str,
    file_id: str,
    request: Request,
) -> Response:
    """
    Thin proxy:
    DELETE https://api.openai.com/v1/containers/{container_id}/files/{file_id}
    """
    logger.info(
        "Relay: delete container file",
        extra={
            "path": f"/v1/containers/{container_id}/files/{file_id}",
            "method": "DELETE",
        },
    )
    return await forward_openai_request(request)
