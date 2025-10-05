from fastapi import APIRouter
from fastapi.responses import FileResponse
import os

router = APIRouter()

@router.get("/openapi.yaml", include_in_schema=False)
async def get_openapi_yaml():
    file_path = os.path.join(os.path.dirname(__file__), "../../openapi_relay_schema.yaml")
    return FileResponse(path=file_path, media_type="text/yaml")
