# ==========================================================
# app/routes/openapi_yaml.py — OpenAPI Specification Route
# ==========================================================
# Exposes the FastAPI-generated OpenAPI 3.1 schema in YAML.
# Mirrors the OpenAI relay's discovery behavior.
# ==========================================================

import yaml
from fastapi import APIRouter, Request, Response
from fastapi.openapi.utils import get_openapi

router = APIRouter(prefix="/v1", tags=["OpenAPI"])

@router.get("/openapi.yaml", include_in_schema=False)
async def get_openapi_yaml(request: Request):
    """
    Generate and return the OpenAPI schema for this relay in YAML format.
    Mirrors OpenAI API structure for discovery and introspection.
    """
    schema = get_openapi(
        title="ChatGPT Team Relay API",
        version="2025-10",
        description="Relay-compatible OpenAI API surface (ChatGPT Team architecture).",
        routes=request.app.routes,
    )
    yaml_schema = yaml.safe_dump(schema, sort_keys=False, allow_unicode=True)
    return Response(content=yaml_schema, media_type="application/x-yaml")
