# ==========================================================
# app/routes/openapi_yaml.py — Dynamic OpenAPI Specification
# ==========================================================
from fastapi import APIRouter, Request, Response
from fastapi.openapi.utils import get_openapi
import yaml

router = APIRouter(tags=["System"])

@router.get("/v1/openapi.yaml", include_in_schema=False)
async def get_openapi_yaml(request: Request):
    """
    Dynamically generates a live OpenAPI YAML spec for the relay.
    """
    openapi_schema = get_openapi(
        title="ChatGPT Team Relay API",
        version="2025.10",
        description="An OpenAI-compatible relay for ChatGPT Plugins and SDK clients.",
        routes=request.app.routes,
    )
    yaml_schema = yaml.safe_dump(openapi_schema, sort_keys=False)
    return Response(content=yaml_schema, media_type="application/x-yaml")
