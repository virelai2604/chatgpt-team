# app/routes/openapi.py
import os
from fastapi import APIRouter, Response, Request

router = APIRouter()

@router.get("/openapi.yaml")
async def serve_openapi_yaml(request: Request):
    """
    Serve the OpenAPI 3.1.0 document as text/yaml.
    Looks for ./openapi.yaml at project root.
    """
    path = os.path.abspath(os.path.join(os.getcwd(), "openapi.yaml"))
    if not os.path.isfile(path):
        return Response(status_code=404, content="openapi.yaml not found", media_type="text/plain")
    with open(path, "r", encoding="utf-8") as f:
        yaml_str = f.read()
    return Response(content=yaml_str, media_type="application/yaml")
