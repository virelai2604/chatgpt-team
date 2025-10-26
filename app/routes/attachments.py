# ==========================================================
# app/routes/attachments.py — BIFL v2.3.4-fp
# ==========================================================
# Unified async passthrough for OpenAI-style attachments.
# Mirrors /v1/files behaviour (upload / retrieve / delete)
# with full streaming and JSON fallback.
# ==========================================================

from fastapi import APIRouter, Request
from app.api.forward import forward_openai

router = APIRouter(prefix="/v1/attachments", tags=["Attachments"])

@router.api_route(
    "/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
)
async def proxy_attachments(request: Request, path: str = ""):
    """
    Transparent async proxy for all /v1/attachments routes.
    Supports multipart uploads, downloads, and metadata queries.
    Example:
        POST /v1/attachments
        GET  /v1/attachments/{id}
    """
    endpoint = f"/v1/attachments/{path}" if path else "/v1/attachments"
    return await forward_openai(request, endpoint)
