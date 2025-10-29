# app/routes/openapi_yaml.py
from fastapi import APIRouter
from fastapi.responses import FileResponse
import os

router = APIRouter(tags=["System"])

@router.get("/v1/openapi.yaml", include_in_schema=False)
async def get_openapi_spec():
    """Serve the static ground-truth OpenAPI spec."""
    path = os.path.join("schemas", "openapi.yaml")
    return FileResponse(path, media_type="application/yaml")
