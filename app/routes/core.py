# app/routes/core.py
# Deprecated shim; prefer app/routes/responses.py
# Kept only if some tests import app.routes.core
from fastapi import APIRouter, Request, Response
from app.routes.services.tool_router import maybe_execute_function_calls
from app.api.forward import forward_openai

router = APIRouter(prefix="/v1", tags=["core"])

@router.post("/responses")
async def create_response(req: Request):
    """
    Legacy entrypoint delegating to /v1/responses behavior.
    """
    body = await req.json()
    if bool(body.get("stream")):
        return await forward_openai(req, "/v1/responses")

    # If someone hits this, just forward to canonical route
    return await forward_openai(req, "/v1/responses")
