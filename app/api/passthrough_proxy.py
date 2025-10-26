# app/api/passthrough_proxy.py — BIFL v2.3.4-fp
import os
from fastapi import APIRouter, Request
from app.api.forward_openai import forward_openai

router = APIRouter(prefix="/v1", tags=["Passthrough"])

@router.api_route("/{path:path}", methods=["GET","POST","PUT","PATCH","DELETE"])
async def passthrough(request: Request, path: str):
    """Forward any unhandled /v1/* path to OpenAI upstream."""
    endpoint = f"/v1/{path}"
    return await forward_openai(request, endpoint)

