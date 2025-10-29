# ==========================================================
# app/routes/openapi_yaml.py — Dynamic OpenAPI Specification
# ==========================================================
# Generates a live YAML schema at /v1/openapi.yaml.
# This endpoint allows plugin validation and keeps in sync
# with FastAPI’s registered routes and metadata.
# ==========================================================

from fastapi import APIRouter, Request, Response
from fastapi.openapi.utils import get_openapi
import yaml

router = APIRouter()

@router.get("/v1/openapi.yaml", include_in_schema=False)
async def get_openapi_yaml(request: Request):
    """
    Returns a live-generated OpenAPI YAML spec for the ChatGPT relay.
    This endpoint must remain dynamic — not a static file.
    """
    openapi_schema = get_openapi(
        title="ChatGPT Team Relay API",
        version="2.3.4-fp",
        description="A relay-compatible OpenAI API interface for ChatGPT Plugins.",
        routes=request.app.routes,
    )
    yaml_schema = yaml.safe_dump(openapi_schema, sort_keys=False)
    return Response(content=yaml_schema, media_type="application/x-yaml")
