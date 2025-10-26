# app/routes/openapi.py — BIFL v2.3.4-fp
from fastapi import APIRouter
from fastapi.openapi.utils import get_openapi
from app.main import app

router = APIRouter(prefix="/v1", tags=["OpenAPI"])

@router.get("/openapi.yaml", include_in_schema=False)
async def openapi_yaml():
    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    import yaml
    return yaml.safe_dump(schema)
