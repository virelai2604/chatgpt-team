"""
actions.py — Custom ChatGPT Actions Endpoints
─────────────────────────────────────────────
Implements any /actions/* endpoints that your OpenAPI schema exposes
to the ChatGPT client. These are NOT part of the public OpenAI REST
surface and are specific to your relay / business logic.
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/actions", tags=["actions"])


@router.get("/ping")
async def ping():
    return JSONResponse(
        {
            "object": "action.ping",
            "message": "Actions API is alive.",
        },
        status_code=200,
    )
