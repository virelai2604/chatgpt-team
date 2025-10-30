from fastapi import APIRouter
from fastapi.responses import FileResponse
import os

router = APIRouter(tags=["OpenAPI"])

@router.get("/v1/openapi.yaml")
async def get_openapi_spec():
    path = os.path.join("schemas", "openapi.yaml")
    return FileResponse(path, media_type="text/yaml")
