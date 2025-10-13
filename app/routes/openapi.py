# app/routes/openapi.py

from fastapi import APIRouter
from fastapi.responses import FileResponse
import os

router = APIRouter()

@router.get("/openapi.yaml")
async def get_openapi_yaml():
    """
    Serve the OpenAPI spec file.
    """
    openapi_path = os.path.join(os.path.dirname(__file__), "../../openapi.yaml")
    return FileResponse(openapi_path, media_type="text/yaml")
